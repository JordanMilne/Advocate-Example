from collections import defaultdict
import codecs
import functools
import os

import advocate
import netifaces
import requests
from flask import request, jsonify, render_template

from json_app import make_json_app, APIException


INTERESTING_FILES = (
    "/etc/hosts",
    os.environ["ADVOCATE_NGINX_CONF"],
)

app = make_json_app(__name__)

# Let's put the validator on easy mode: No port whitelisting, IPv6 allowed.
validator = advocate.AddrValidator(
    allow_ipv6=True,
    allow_6to4=True,
    allow_teredo=True,
    allow_dns64=True,
    hostname_blacklist={
        "*.yahoo.com", "yahoo.com", "*.foocorp.internal", "foocorp.internal",
    },
    port_blacklist={8080, 22, },
)
advocate_wrapper = advocate.RequestsAPIWrapper(validator)


def fetch_preview(url):
    sess = advocate_wrapper.Session()
    sess.headers["User-Agent"] = \
        "Advocate Previewer 0.1 (advocate.saynotolinux.com)"

    req = advocate.Request("GET", url)
    # Don't let people tie up the server forever
    resp = sess.send(req.prepare(), timeout=1.5, stream=True)

    # Decode gzip if we get it, some servers send it even if you don't want it
    resp.raw.read = functools.partial(resp.raw.read, decode_content=True)

    # Don't bother fetching the whole thing, we only want the first little bit
    encoding = "utf-8"
    if resp.encoding:
        encoding = resp.encoding
    with codecs.getreader(encoding)(resp.raw, "ignore") as reader:
        # We should use `Range` to indicate that this is all we care about,
        # but in practice this causes issues with `Content-Encoding: gzip`.
        # Thank UAs for never properly implementing `Transfer-Encoding` / `TE`
        preview = reader.read(1024)
        # Give an indication that the preview is truncated
        if reader.read(1):
            preview += " [...]"
    return preview


def get_interface_ips():
    ips = defaultdict(dict)
    for interface in netifaces.interfaces():
        if_families = netifaces.ifaddresses(interface)
        for family_name in {"AF_INET", "AF_INET6"}:
            family_num = getattr(netifaces, family_name)
            addrs = if_families.get(family_num, [])
            if addrs:
                ips[interface][family_name] = [x.get("addr", "") for x in addrs]
    return ips


@app.route('/get_preview', methods=["GET"])
def get_preview():
    url = request.args.get("url")
    if not url:
        return "Please specify a url!"
    try:
        preview = fetch_preview(url)
    except advocate.UnacceptableAddressException:
        raise APIException(400, "That URL points to a forbidden resource")
    except requests.Timeout:
        raise APIException(504, "Requested URL took too long to fetch")
    except requests.RequestException as e:
        raise APIException(500, "Failed to fetch the URL: %s" % e)

    return jsonify(preview=preview)


@app.route("/", methods=["GET"])
def index():
    interesting_contents = {}
    for interesting_path in INTERESTING_FILES:
        with file(interesting_path, "r") as f:
            interesting_contents[interesting_path] = f.read()
    return render_template(
        "index.html",
        validator=validator,
        interfaces=get_interface_ips(),
        interesting_files=interesting_contents,
    )

if __name__ == '__main__':
    app.run()
