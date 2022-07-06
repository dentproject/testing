"""Utility functions and classes
"""
import aiofiles
import aiohttp


class Host:
    """
    Class representing a host
    """

    def __init__(self, ip, username, password):
        """
        Initializliation for the Host class

        Args:
            ip(str): IP address of the host
            username (str): Username for logging in to the host
            password (str); Password for logging in to the host
        """
        self.username = username
        self.ip = ip
        self.password = password


async def download_file(http_url, out_file):
    """
    Download file from a given HTTP URL

    Args:
        http_url(str): URL string
        out_file(str): Path to save the downloaded file

    Raises:
        Exception: Generic errors
    """
    try:
        async with aiofiles.open(out_file, "ab") as f, aiohttp.ClientSession() as session:
            async with session.get(http_url) as response:
                print(out_file)
                while True:
                    chunk = await response.content.read(1024)
                    if not chunk:
                        break
                    await f.write(chunk)
                    await f.flush()
    except Exception as e:
        raise


def check_asyncio_results(results, op):
    exception_occured = False
    failed_devices = []
    for r in results:
        if isinstance(r, Exception):
            exception_occured = True
            if "extra_info" in dir(r):
                failed_devices.append(r.extra_info)
    if exception_occured:
        e = Exception(f"Failure in {op} for one more devices")
        e.extra_info = failed_devices
        raise e
