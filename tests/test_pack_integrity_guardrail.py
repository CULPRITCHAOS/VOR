import os
import pytest
from neuralogix.core.packs.loader import PackLoader

def test_all_packs_integrity():
    """Fail CI if any pack in data/packs fails manifest validation."""
    packs_dir = "data/packs"
    if not os.path.exists(packs_dir):
        pytest.skip("data/packs directory not found")
        
    failed_packs = []
    for pack_name in os.listdir(packs_dir):
        pack_path = os.path.join(packs_dir, pack_name)
        # Only check folders that contain a manifest.json
        if os.path.isdir(pack_path) and os.path.exists(os.path.join(pack_path, "manifest.json")):
            try:
                PackLoader().load_pack(pack_path)
            except ValueError as e:
                failed_packs.append(f"{pack_name}: {e}")
    
    if failed_packs:
        pytest.fail("Integrity check failed for the following packs:\n" + "\n".join(failed_packs))
