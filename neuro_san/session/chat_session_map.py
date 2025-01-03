
# Copyright (C) 2023-2025 Cognizant Digital Business, Evolutionary AI.
# All Rights Reserved.
# Issued under the Academic Public License.
#
# You can be released from the terms, and requirements of the Academic Public
# License by purchasing a commercial license.
# Purchase of a commercial license is mandatory for any use of the
# neuro-san SDK Software in commercial settings.
#
# END COPYRIGHT
from typing import Any
from typing import Dict
from typing import List

import logging
import threading
import traceback
import uuid

from asyncio import gather

from datetime import datetime
from datetime import timedelta

from leaf_common.asyncio.asyncio_executor import AsyncioExecutor

from neuro_san.internals.chat.chat_session import ChatSession


class ChatSessionMap:
    """
    Class that handles the storage of ChatSessions on a per-session basis.
    The idea is that a single instance is stored as a global within any given
    service implementation.
    """

    # Constant for how long ChatSession are allowed to be idle
    # before they are pruned.  See prune() below.
    IDLE_HOURS: int = 2

    def __init__(self, init_argument: Dict[str, Any]):
        """
        Constructor

        :param init_argument: A dictionary of args passed in at construct time
                Some flask/quart app infra only allows a single argument coming into the constructor,
                so we need to pass > 1 (if needed) as a dictionary.
        """

        self.lock = threading.Lock()
        self.logger = logging.getLogger(self.__class__.__name__)

        # Store access to the globals
        self.chat_sessions: Dict[str, ChatSession] = init_argument.get("chat_sessions")
        self.asyncio_executor: AsyncioExecutor = init_argument.get("executor")

    def get_chat_session(self, session_id: str = None) -> ChatSession:
        """
        :param session_id: A session id whose ChatSession we will return
                    If None is given, we return something for a default session.
        :return: The ChatSession belonging to the given session_id
                Can return None if the session_id has never been seen before
        """
        chat_session: ChatSession = None

        # When getting ChatSessions, Use the lock
        # Make it short and sweet.
        session_key = self._get_session_key(session_id)
        with self.lock:
            chat_session = self.chat_sessions.get(session_key)

        return chat_session

    def register_chat_session(self, chat_session: ChatSession, session_id: str = None) -> str:
        """
        :param chat_session: The ChatSession instance to store
                    It is possible to pass in None here to remove the chat_session
                    from the store.
        :param session_id: A session_id whose ChatSession we will return
                    If None is given, we do something for a default session.
        :return: The key used to index the ChatSessions.
        """
        old_chat_session: ChatSession = None
        remove_old_chat_session: bool = False

        session_key = self._get_session_key(session_id)

        # When registering ChatSessions, use the lock
        with self.lock:

            if session_key in self.chat_sessions:
                # Tear down any current occupant's resources
                old_chat_session = self.chat_sessions[session_key]
                if old_chat_session != chat_session:
                    remove_old_chat_session = True

            if chat_session is None:
                if session_key in self.chat_sessions:
                    # Remove the chat_session from the store
                    del self.chat_sessions[session_key]
            else:
                # Put the new chat_session in the store.
                self.chat_sessions[session_key] = chat_session

        if remove_old_chat_session and old_chat_session is not None:
            # Do this outside the lock
            old_chat_session.delete_resources()

        return session_key

    def _get_session_key(self, session_id: str = None) -> str:
        """
        :param session_id: A session_id whose key we will return
        :return: They string key for the session, or if no session was given,
                 we return a key for a default session.
                 The idea is to treat this as somewhat of a unique hash for sessions.
        """

        if session_id is None:
            session_key = str(uuid.uuid4())
        elif not isinstance(session_id, str):
            raise ValueError(f"Expected session {session_id} to be a string")
        else:
            # The session key itself has been passed in as a string
            session_key: str = str(session_id)

        return session_key

    def prune(self):
        """
        Prune resources for older unused ChatSessions.
        """
        prune_time = datetime.now()
        idle_time = timedelta(hours=self.IDLE_HOURS)

        chat_sessions_to_delete: List[ChatSession] = []
        keys_to_delete: List[str] = []

        # Use the lock so no one else can modify while we are cleaning up.
        with self.lock:

            # We want to delete the resources of all the existing chat_sessions
            # that have not had any activity but need to keep their references
            # around after we clear them out from the list so we can do the
            # delete_resources() outside the lock.
            for session_key, chat_session in self.chat_sessions.items():

                # See if the chat_session has idled out.
                last_input_timestamp = chat_session.get_last_input_timestamp()
                if last_input_timestamp + idle_time < prune_time:

                    # Idled out. Add to the lists.
                    # Make a list of keys to delete from the map outside this loop.
                    keys_to_delete.append(session_key)

                    # Keep references to the chat_sessions to delete so they
                    # won't be garbage collected when they are not referenced
                    # by the chat_session map any more.
                    chat_sessions_to_delete.append(chat_session)

            # Since we still have the lock, delete the keys from the chat_sessions map
            for session_key in keys_to_delete:
                # Remove the chat_session from the store
                del self.chat_sessions[session_key]

        # Now that we are outside the lock, actually to do the resource cleanup
        # for each of the chat_sessions we want to delete.
        self.asyncio_executor.submit("prune", self._delete_resources, chat_sessions_to_delete)

    def cleanup(self):
        """
        Clean up resources associated with the instance

        ChatSession implementations use a stateful OpenAI API where there
        are notions of "threads" and "assistants" stored on their server side
        that need to be cleaned up, otherwise we run into hangs because of
        resource limits.

        A single ChatSession instance might use > 1 thread (maybe) or
        > 1 assistant (definitely) to do its work.

        The delete_resources() call used here goes ahead and calls the OpenAI API
        that says "we don't need these threads and/or assistants server-side any more."

        We stil use a lock here for the whole thing even though cleanup() only happens when
        the service is coming down - like a pod is being rotated or something like that.
        """
        to_delete: List[ChatSession] = []

        # Use the lock so no one else can modify while we are cleaning up.
        with self.lock:

            # We want to delete the resources of all the existing ChatSessions
            # but need to keep their references around after we clear out
            # the list so we can do the delete_resources() outside the lock.
            to_delete = list(self.chat_sessions.values())

            # Clear out the entries in the dictionary so we do not
            # hold the lock so long.
            self.chat_sessions.clear()

        # Now go ahead and delete the resources outside the lock
        self.asyncio_executor.submit("cleanup", self._delete_resources, to_delete)

    async def _delete_resources(self, to_delete: List[ChatSession]):
        """
        Delete the chat_sessions resources on the OpenAI service-side.
        This can take some time, so do not call this while holding the lock.

        :param to_delete: A list of ChatSession whose resources are to
                    be deleted.
        """
        if to_delete is None:
            return

        if len(to_delete) > 0:

            delete_resources: List[Any] = []
            for chat_session in to_delete:
                # Add the asyncio coroutine for cleaning up to the list
                delete_resources.append(chat_session.delete_resources())

            self.logger.info("Awaiting %d from delete_resources", len(delete_resources))
            results = await gather(*delete_resources, return_exceptions=True)
            for result in results:
                if isinstance(result, Exception):
                    print(f"{result}")
                    traceback.print_tb(result.__traceback__)
