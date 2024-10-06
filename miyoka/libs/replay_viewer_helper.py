from logging import Logger
import hmac

try:
    import streamlit as st
except (ImportError, NotImplementedError) as e:
    print(
        "WARN: streamlit is not installed. You cannot run replay viewer in this environment."
    )


class ReplayViewerHelper:
    def __init__(
        self,
        logger: Logger,
        password: str,
        player_name: str,
        debug_mode: bool,
        *args,
        **kwargs,
    ):
        self.logger = logger
        self.password = password
        self.player_name = player_name
        self._debug_mode = debug_mode

    @property
    def debug_mode(self):
        return self._debug_mode

    def check_password(self):
        """Returns `True` if the user had the correct password."""

        def password_entered():
            """Checks whether a password entered by the user is correct."""
            if hmac.compare_digest(st.session_state["password"], self.password):
                st.session_state["password_correct"] = True
                del st.session_state["password"]  # Don't store the password.
            else:
                st.session_state["password_correct"] = False

        # Return True if the password is validated.
        if self.password == "None" or st.session_state.get("password_correct", False):
            return True

        if not self.password:
            st.error(
                "❌ Password is not set to this Miyoka server. Ask the administrator if they correctly set it."
            )
            return False

        # Show input for password.
        st.text_input(
            "Password", type="password", on_change=password_entered, key="password"
        )
        if "password_correct" in st.session_state:
            st.error("😕 Password incorrect")
        return False
