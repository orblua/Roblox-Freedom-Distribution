from web_server._logic import web_server_handler, server_path
import util.const
import struct
import gzip
import zlib
import re
import io


def decompress_gzip(data, file_handle) -> None:
    """
    Decompress a gzip compressed string into a file handle.
    Modified from `gzip.decompress` to write directly to disk.
    """
    while True:
        fp = io.BytesIO(data)
        if gzip._read_gzip_header(fp) is None:  # type: ignore
            return
        # Use a zlib raw deflate compressor
        do = zlib.decompressobj(wbits=-zlib.MAX_WBITS)
        # Read all the data except the header
        decompressed = do.decompress(data[fp.tell():])
        if not do.eof or len(do.unused_data) < 8:
            raise EOFError("Compressed file ended before the end-of-stream "
                           "marker was reached")
        crc, length = struct.unpack("<II", do.unused_data[:8])
        if crc != zlib.crc32(decompressed):
            raise gzip.BadGzipFile("CRC check failed")
        if length != (len(decompressed) & 0xffffffff):
            raise gzip.BadGzipFile("Incorrect length of data produced")
        file_handle.write(decompressed)
        data = do.unused_data[8:].lstrip(b"\x00")


@server_path("/v1/places/([0-9]+)/symbolic-links", regex=True)
def _(self: web_server_handler, match: re.Match[str]) -> bool:
    '''
    Dummy function to return an empty list of packages.
    Rōblox's "package" feature is not used in RFD.
    '''
    self.send_json({
        "previousPageCursor": None,
        "nextPageCursor": None,  # "11924224825_1_6f7d678fdda36d18945b54748884df34",
        "data": []
    })
    return True


@server_path("/ide/publish/UploadExistingAsset")
def _(self: web_server_handler) -> bool:

    # Returns false if the thing trying to be saved isn't the place we're in.
    if self.query.get('assetId') != str(util.const.DEFAULT_PLACE_ID):
        return False

    place_config = self.server.game_config.game_setup.place
    if not place_config.enable_saveplace:
        return False

    zipped_content = self.read_content()
    with open(place_config.path, 'wb') as f:
        decompress_gzip(zipped_content, f)

    self.send_json([])
    return True