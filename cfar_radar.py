
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

INPUT = "radar_data.csv"
OUTPUT = "cfar_detections.csv"

def ca_cfar_2d(power, train_r=6, train_d=5, guard_r=1, guard_d=1, pfa=1e-3):
    rows, cols = power.shape
    detections = []
    det_map = np.zeros_like(power, dtype=np.uint8)

    total_r = train_r + guard_r
    total_d = train_d + guard_d

    # Approximate number of training cells
    outer = (2*total_r + 1) * (2*total_d + 1)
    guard = (2*guard_r + 1) * (2*guard_d + 1)
    n_train = max(1, outer - guard)

    # CA-CFAR exponential-noise scaling factor
    alpha = n_train * (pfa ** (-1.0 / n_train) - 1.0)

    for r in range(total_r, rows-total_r):
        for d in range(total_d, cols-total_d):
            window = power[r-total_r:r+total_r+1, d-total_d:d+total_d+1]
            mask = np.ones(window.shape, dtype=bool)

            gr0 = total_r - guard_r
            gr1 = total_r + guard_r + 1
            gd0 = total_d - guard_d
            gd1 = total_d + guard_d + 1
            mask[gr0:gr1, gd0:gd1] = False

            training = window[mask]
            noise_est = np.mean(training)
            threshold = alpha * noise_est
            cell = power[r, d]

            if cell > threshold:
                det_map[r, d] = 1
                detections.append((r, d, float(cell), float(threshold)))

    return np.array(detections, dtype=float), det_map

def main():
    df = pd.read_csv(INPUT, index_col=0)
    power = df.values.astype(float)

    detections, det_map = ca_cfar_2d(power)

    if len(detections):
        out = pd.DataFrame(
            detections,
            columns=["range_bin", "doppler_bin", "power", "threshold"]
        )
        out.to_csv(OUTPUT, index=False)
        print(f"Detections: {len(out)}")
        print(out.head(20).to_string(index=False))
    else:
        pd.DataFrame(columns=["range_bin","doppler_bin","power","threshold"]).to_csv(OUTPUT, index=False)
        print("No detections.")

    plt.figure(figsize=(10, 6))
    plt.imshow(10*np.log10(power + 1e-9), aspect="auto", origin="lower")
    ys, xs = np.where(det_map > 0)
    plt.scatter(xs, ys, s=12, facecolors="none", edgecolors="red")
    plt.xlabel("Doppler bin")
    plt.ylabel("Range bin")
    plt.title("2D CA-CFAR detections")
    plt.colorbar(label="Relative power (dB)")
    plt.tight_layout()
    plt.savefig("cfar_detection_map.png", dpi=160)
    plt.show()

if __name__ == "__main__":
    main()
