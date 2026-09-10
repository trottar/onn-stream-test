from .iptv_org import IPTVOrgPlugin
from .games import GamesPlugin


PLUGINS = {
    "iptv_org": IPTVOrgPlugin(),
    "games": GamesPlugin(),
}
# PRIVYHUB_A4_PLUGIN_LIFECYCLE_SHUTDOWN_V1
def shutdown_plugins() -> list[str]:
    """Stop plugin-owned runtime state before the companion process exits.

    Games deliberately reuses its normal, validated `stop` action instead of
    inventing a parallel shutdown implementation. Other plugins can expose a
    `shutdown()` method in the future and will be called generically.
    """

    errors: list[str] = []

    for plugin_id, plugin in reversed(
        list(PLUGINS.items())
    ):
        try:
            shutdown = getattr(
                plugin,
                "shutdown",
                None,
            )

            if callable(shutdown):
                shutdown()
                continue

            if plugin_id == "games":
                stop_handler = getattr(
                    plugin,
                    "handle_post",
                    None,
                )

                if not callable(
                    stop_handler
                ):
                    raise RuntimeError(
                        "Games plugin has no stop handler"
                    )

                stop_handler(
                    "stop",
                    "",
                )

        except Exception as exc:
            errors.append(
                f"{plugin_id}: {exc}"
            )

    return errors
