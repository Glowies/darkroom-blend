# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "oiio-python>=3.0.10.0.1",
# ]
# ///
import os
import argparse
import tempfile
import OpenImageIO as oiio

def sync_metadata_final(target_dir, source_dir):
    source_files = {os.path.splitext(f)[0]: f for f in os.listdir(source_dir)}

    for filename in os.listdir(target_dir):
        if not filename.lower().endswith(".exr"):
            continue

        stem = os.path.splitext(filename)[0]
        if stem not in source_files:
            continue

        target_path = os.path.join(target_dir, filename)
        source_path = os.path.join(source_dir, source_files[stem])
        
        fd, temp_path = tempfile.mkstemp(suffix=".exr", dir=target_dir)
        os.close(fd)

        t_input = oiio.ImageInput.open(target_path)
        s_input = oiio.ImageInput.open(source_path)

        if not t_input or not s_input:
            print(f"Error opening files for {filename}")
            continue

        tgt_spec = t_input.spec()
        src_spec = s_input.spec()

        # 1. Capture the critical structural attributes from the TARGET
        # We use getattribute to get the precise internal values
        target_compression = tgt_spec.getattribute("compression")
        target_format = tgt_spec.format
        t_w = tgt_spec.tile_width
        t_h = tgt_spec.tile_height

        # 2. Create the new spec starting with the TARGET's layout
        new_spec = oiio.ImageSpec(tgt_spec)
        
        # 3. Wipe and replace the extra metadata from the SOURCE
        new_spec.extra_attribs = src_spec.extra_attribs
        
        # 4. Re-inject the target's structural attributes using attribute()
        # This ensures the 'extra_attribs' copy doesn't overwrite these
        if target_compression:
            new_spec.attribute("compression", target_compression)
        
        # Ensure tile/scanline state is preserved
        new_spec.tile_width = t_w
        new_spec.tile_height = t_h
        new_spec.format = target_format

        out = oiio.ImageOutput.create(temp_path)
        if out:
            # Open the output with our hybrid spec
            out.open(temp_path, new_spec)
            
            # Perform the raw copy
            print(f"Syncing: {filename} (preserving {target_compression} compression)")
            success = out.copy_image(t_input)
            
            out.close()
            t_input.close()
            s_input.close()

            if success:
                os.replace(temp_path, target_path)
            else:
                print(f"Error during raw copy: {out.geterror()}")
                if os.path.exists(temp_path):
                    os.remove(temp_path)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("target_dir")
    parser.add_argument("source_dir")
    args = parser.parse_args()
    sync_metadata_final(args.target_dir, args.source_dir)
