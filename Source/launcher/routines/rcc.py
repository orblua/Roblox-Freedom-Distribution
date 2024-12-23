import web_server._logic as web_server_logic
from ..startup_scripts import rcc_server
from . import _logic as logic
import util.const as const
import assets.serialisers
import game_config.structure
import util.resource
import util.versions
import dataclasses
import subprocess
import functools
import util.ssl
import game_config
import json
import os


class obj_type(logic.bin_ssl_entry, logic.server_entry):
    local_args: 'arg_type'
    BIN_SUBTYPE = util.resource.bin_subtype.SERVER

    @functools.cache
    def retr_version(self) -> util.versions.rōblox:
        return self.game_config.game_setup.roblox_version

    def save_place_file(self) -> None:
        '''
        Parses and copies the place file (specified in the config file) to the asset cache.
        '''
        config = self.game_config

        def parse(data: bytes) -> bytes:
            return assets.serialisers.parse(
                data, {assets.serialisers.method.rbxl}
            )

        place_uri = config.server_core.place_file.rbxl_uri
        if place_uri is None:
            raise Exception('Place file does not exist.')

        cache = config.asset_cache
        rbxl_data = parse(place_uri.extract())
        cache.add_asset(self.local_args.place_iden, rbxl_data)

        try:
            thumbnail_data = config.server_core.metadata.icon_uri.extract()
            cache.add_asset(const.THUMBNAIL_ID_CONST, thumbnail_data)
        except Exception as e:
            pass

        if place_uri.is_online and config.server_core.place_file.enable_saveplace:
            print(
                'Warning: config option "enable_saveplace" is redundant ' +
                'when the place file is an online resource.'
            )

    def save_app_setting(self) -> str:
        '''
        Simply modifies `AppSettings.xml` to point to correct host name.
        '''
        path = self.get_versioned_path('AppSettings.xml')
        app_base_url = self.local_args.get_app_base_url()
        with open(path, 'w', encoding='utf-8') as f:
            f.write('\n'.join([
                """<?xml version="1.0" encoding="UTF-8"?>""",
                """<Settings>""",
                f"""\t<BaseUrl>{app_base_url}</BaseUrl>""",
                """</Settings>""",
            ]))
        return path

    def save_starter_scripts(self) -> None:
        server_path = self.get_versioned_path(os.path.join(
            'Content',
            'Scripts',
            'CoreScripts',
            'RFDStarterScript.lua',
        ))
        with open(server_path, 'w', encoding='utf-8') as f:
            rcc_script = rcc_server.get_script(self.game_config)
            f.write(rcc_script)

    def save_gameserver(self) -> str:
        base_url = self.local_args.get_base_url()
        path = self.get_versioned_path('GameServer.json')

        with open(path, 'w', encoding='utf-8') as f:
            json.dump({
                "Mode": "GameServer",
                "GameId": 13058,
                "Settings": {
                    "Type":
                        "Avatar",
                    "PlaceId":
                        self.local_args.place_iden,
                    "GameId":
                        "Test",
                    "MachineAddress":
                        base_url,
                    "PlaceFetchUrl":
                        f"{base_url}/asset/?id={self.local_args.place_iden}",
                    "MaxPlayers":
                        int(1e9),
                    "PreferredPlayerCapacity":
                        int(1e9),
                    "CharacterAppearance":
                        f"{base_url}/v1.1/avatar-fetch",
                    "MaxGameInstances":
                        1,
                    "GsmInterval":
                        5,
                    "ApiKey":
                        "",
                    "DataCenterId":
                        "69420",
                    "PlaceVisitAccessKey":
                        "",
                    "UniverseId":
                        13058,
                    "MatchmakingContextId":
                        1,
                    "CreatorId":
                        1,
                    "CreatorType":
                        "User",
                    "PlaceVersion":
                        1,
                    "BaseUrl":
                        f"{base_url}/.127.0.0.1",
                    "JobId":
                        "Test",
                    "PreferredPort":
                        self.local_args.rcc_port_num,
                },
                "Arguments": {},
            }, f)
        return path

    def make_rcc_popen(self) -> None:
        return self.make_popen(
            [
                self.get_versioned_path('RCCService.exe'),

                f'-PlaceId:{self.local_args.place_iden}',

                '-LocalTest', self.get_versioned_path(
                    'GameServer.json',
                ),

                '-SettingsFile', self.get_versioned_path(
                    'DevSettingsFile.json',
                ),

                *(() if self.local_args.quiet else ('-verbose',)),
            ],
            stdin=subprocess.PIPE,
            cwd=self.get_versioned_path(),

            # This suppresses the "To enable debug output, run with the -verbose flag"
            # which prints if verbosity is disabled.
            stdout=subprocess.PIPE if self.local_args.quiet else None,
        )

    def process(self) -> None:
        print(
            "[UDP %d]: initialising Rōblox Cloud Compute" %
            self.local_args.rcc_port_num
        )
        self.save_starter_scripts()
        self.save_place_file()
        self.save_app_setting()
        self.save_ssl_cert(
            include_system_certs=True,
        )

        self.save_gameserver()
        if not self.local_args.skip_popen:
            self.make_rcc_popen()


@dataclasses.dataclass
class arg_type(logic.bin_ssl_arg_type):
    obj_type = obj_type

    rcc_port_num: int | None
    game_config: game_config.obj_type
    skip_popen: bool = False
    quiet: bool = False
    # TODO: fix the way place idens work.
    place_iden: int = const.PLACE_IDEN_CONST
    web_port: web_server_logic.port_typ = web_server_logic.port_typ(
        port_num=80,
        is_ssl=False,
        is_ipv6=False,
    ),  # type: ignore

    def get_base_url(self) -> str:
        return (
            f'http{"s" if self.web_port.is_ssl else ""}://' +
            f'localhost:{self.web_port.port_num}'
        )

    def get_app_base_url(self) -> str:
        return f'{self.get_base_url()}/'
