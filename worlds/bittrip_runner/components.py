from worlds.LauncherComponents import Component, Type, components, icon_paths, launch

ICON_NAME = "BIT.TRIP RUNNER"
ICON_RESOURCE = "assets/icon.png"
"""Path of the icon inside this package, for pkgutil."""


def run_client(*args: str) -> None:
    from .client.launch import launch_client

    launch(launch_client, name="BIT.TRIP RUNNER Client", args=args)


components.append(
    Component(
        "BIT.TRIP RUNNER Client",
        func=run_client,
        game_name="BIT.TRIP RUNNER",
        component_type=Type.CLIENT,
        supports_uri=True,
        icon=ICON_NAME,
        description="Connect BIT.TRIP RUNNER (Windows, Steam) to a multiworld.",
    )
)

# "ap:" paths are read straight out of the package, so this works from source and from a zipped .apworld.
icon_paths[ICON_NAME] = f"ap:{__package__}/{ICON_RESOURCE}"
