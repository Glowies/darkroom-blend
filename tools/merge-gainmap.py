"""Merge SDR / HDR render pairs into gain map AVIFs with avifgainmaputil.

For every "<name><hdr-suffix>.<ext>" in the input directory with a matching
"<name><sdr-suffix>.<ext>", writes "<name>.avif" to the output directory. The
SDR render is the base image (shown by viewers without gain map support) and
the HDR render the alternate image.

The CICP (primaries/transfer/matrix) of each render is read from its metadata,
as written by Blender, unless given with --cicp-base / --cicp-alternate. They
must describe how the file was actually encoded: avifgainmaputil uses them to
decode the inputs, so a wrong matrix shifts the colors of the base image.

avifgainmaputil is not on conda-forge; install libavif (e.g. brew install libavif).
Arguments not recognized here are passed on to avifgainmaputil, e.g. --grid 2x2.
"""

import argparse
import os
import shutil
import subprocess
import sys

import OpenImageIO as oiio

# Input formats avifgainmaputil can read
EXTENSIONS = (".avif", ".png", ".jpg", ".jpeg")


def read_cicp(path):
    """ "P/T/M" from the CICP metadata of the image at path, or None if absent."""
    image = oiio.ImageInput.open(path)
    if not image:
        sys.exit(f"Error: could not open '{path}': {oiio.geterror()}")
    cicp = image.spec().getattribute("CICP")
    image.close()
    if not cicp:
        return None
    primaries, transfer, matrix, _full_range = cicp
    return f"{primaries}/{transfer}/{matrix}"


def find_pairs(input_dir, sdr_suffix, hdr_suffix):
    """[(name, sdr_path, hdr_path)] for the render pairs in input_dir."""
    files = {}
    for filename in os.listdir(input_dir):
        stem, ext = os.path.splitext(filename)
        if ext.lower() in EXTENSIONS:
            files.setdefault(stem, os.path.join(input_dir, filename))

    pairs = []
    for stem, hdr_path in sorted(files.items()):
        if not stem.endswith(hdr_suffix):
            continue
        name = stem.removesuffix(hdr_suffix)
        sdr_path = files.get(name + sdr_suffix)
        if sdr_path is None or sdr_path == hdr_path:
            print(f"Skipping '{os.path.basename(hdr_path)}': no matching SDR render")
            continue
        pairs.append((name, sdr_path, hdr_path))
    return pairs


def merge_pair(tool, sdr_path, hdr_path, output_path, args, extra_args):
    """Run avifgainmaputil combine for one pair. Returns True on success."""
    cicp_base = args.cicp_base or read_cicp(sdr_path)
    cicp_alternate = args.cicp_alternate or read_cicp(hdr_path)
    for label, path, cicp in (
        ("--cicp-base", sdr_path, cicp_base),
        ("--cicp-alternate", hdr_path, cicp_alternate),
    ):
        if cicp is None:
            print(f"  Error: '{path}' has no CICP metadata, pass {label}")
            return False

    command = [
        tool,
        "combine",
        sdr_path,
        hdr_path,
        output_path,
        "--cicp-base",
        cicp_base,
        "--cicp-alternate",
        cicp_alternate,
        # The CICP above is authoritative, ignore any embedded ICC profile
        "--ignore-profile",
    ]
    for flag, value in (
        ("--qgain-map", args.qgain_map),
        ("--depth-gain-map", args.depth_gain_map),
        ("--downscaling", args.downscaling),
        ("--yuv-gain-map", args.yuv_gain_map),
        ("--max-headroom", args.max_headroom),
        ("--qcolor", args.qcolor),
        ("--depth", args.depth),
        ("--yuv", args.yuv),
        ("--speed", args.speed),
        ("--jobs", args.jobs),
    ):
        if value is not None:
            command += [flag, str(value)]
    command += extra_args

    print(f"  CICP base {cicp_base}, alternate {cicp_alternate}")
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  Error: {(result.stderr or result.stdout).strip()}")
        return False
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Merge SDR / HDR render pairs into gain map AVIFs.",
        epilog="Unrecognized arguments are passed on to avifgainmaputil combine.",
    )
    parser.add_argument("input", help="Directory containing the SDR / HDR renders")
    parser.add_argument("output", help="Directory to write the gain map AVIFs to")
    parser.add_argument(
        "--sdr-suffix",
        default="SDR",
        help='Suffix of the SDR renders, may be empty (default: "SDR")',
    )
    parser.add_argument(
        "--hdr-suffix", default="HDR", help='Suffix of the HDR renders (default: "HDR")'
    )
    parser.add_argument(
        "--cicp-base",
        metavar="P/T/M",
        help="CICP of the SDR renders (default: read from their metadata)",
    )
    parser.add_argument(
        "--cicp-alternate",
        metavar="P/T/M",
        help="CICP of the HDR renders (default: read from their metadata)",
    )

    gainmap = parser.add_argument_group("avifgainmaputil options")
    gainmap.add_argument(
        "--qgain-map",
        type=int,
        default=90,
        help="Gain map quality, 0-100 where 100 is lossless (default: 90)",
    )
    gainmap.add_argument(
        "--depth-gain-map",
        type=int,
        choices=(8, 10, 12),
        default=8,
        help="Gain map bit depth (default: 8)",
    )
    gainmap.add_argument(
        "--downscaling",
        type=int,
        default=1,
        help="Gain map downscaling factor (default: 1)",
    )
    gainmap.add_argument(
        "--yuv-gain-map",
        choices=("444", "422", "420", "400"),
        help="Gain map YUV format, 400 for a single channel gain map",
    )
    gainmap.add_argument(
        "--max-headroom", type=float, help="Maximum HDR headroom, in stops"
    )
    gainmap.add_argument(
        "-q",
        "--qcolor",
        type=int,
        help="Base image quality, 0-100 where 100 is lossless "
        "(avifgainmaputil default: 60)",
    )
    gainmap.add_argument(
        "-d", "--depth", type=int, choices=(0, 8, 10, 12), help="Base image bit depth"
    )
    gainmap.add_argument(
        "-y",
        "--yuv",
        choices=("444", "422", "420", "400"),
        help="Base image YUV format",
    )
    gainmap.add_argument(
        "-s", "--speed", type=int, help="Encoder speed, 0-10 (slowest-fastest)"
    )
    gainmap.add_argument("-j", "--jobs", help="Worker threads, or 'all'")
    gainmap.add_argument(
        "--avifgainmaputil",
        default="avifgainmaputil",
        help="Path to the avifgainmaputil executable",
    )

    args, extra_args = parser.parse_known_args()

    tool = shutil.which(args.avifgainmaputil)
    if tool is None:
        sys.exit(
            f"Error: '{args.avifgainmaputil}' not found. Install libavif "
            "(e.g. brew install libavif) or pass --avifgainmaputil."
        )
    if not os.path.isdir(args.input):
        sys.exit(f"Error: The input directory '{args.input}' does not exist.")
    if args.sdr_suffix == args.hdr_suffix:
        sys.exit("Error: --sdr-suffix and --hdr-suffix must differ.")

    pairs = find_pairs(args.input, args.sdr_suffix, args.hdr_suffix)
    if not pairs:
        sys.exit(f"No SDR / HDR render pairs found in '{args.input}'.")

    os.makedirs(args.output, exist_ok=True)
    failed = 0
    for i, (name, sdr_path, hdr_path) in enumerate(pairs, 1):
        output_path = os.path.join(args.output, f"{name}.avif")
        print(f"[{i}/{len(pairs)}] {name}")
        if not merge_pair(tool, sdr_path, hdr_path, output_path, args, extra_args):
            failed += 1

    print(f"\nMerged {len(pairs) - failed} of {len(pairs)} pairs.")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
