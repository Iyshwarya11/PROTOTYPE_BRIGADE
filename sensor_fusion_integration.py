"""
Small integration example for the main sensor-fusion POC.
Run lens blockage first, then use its camera confidence to decide
whether radar + thermal should dominate.
"""
from lens_blockage_detection import health_features

def fused_confidence(radar_conf, thermal_conf, camera_conf):
    # Example weighted average for demonstration only.
    return 0.50*radar_conf + 0.35*thermal_conf + 0.15*camera_conf

if __name__ == "__main__":
    health = health_features("blocked_camera.png")
    radar = 0.95
    thermal = 0.92
    camera = health["camera_confidence"]

    fused = fused_confidence(radar, thermal, camera)

    print("Camera status:", health["status"])
    print(f"Radar confidence:   {radar*100:.1f}%")
    print(f"Thermal confidence: {thermal*100:.1f}%")
    print(f"Camera confidence:  {camera*100:.1f}%")
    print(f"Fused confidence:   {fused*100:.1f}%")

    if health["status"] != "HEALTHY":
        print("FAIL-SAFE: reduce camera weight; rely primarily on radar + thermal.")
