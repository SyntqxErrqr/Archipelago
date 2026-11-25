from worlds.LauncherComponents import Component, Type, components, launch


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
    )
)
