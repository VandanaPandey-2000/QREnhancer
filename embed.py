# import cv2
# import numpy as np
# import random
# import hashlib

# def is_safe_zone(qr_img, x, y, w, h, module_size):
#     finder_size = 7 * module_size
#     quiet_zone = 4 * module_size

#     if ((x < finder_size + quiet_zone and y < finder_size + quiet_zone) or
#         (x > qr_img.shape[1] - finder_size - quiet_zone and y < finder_size + quiet_zone) or
#         (x < finder_size + quiet_zone and y > qr_img.shape[0] - finder_size - quiet_zone)):
#         return False

#     timing_pos = finder_size + quiet_zone - module_size // 2
#     if abs(y - timing_pos) < module_size // 2 + 1 or abs(x - timing_pos) < module_size // 2 + 1:
#         return False

#     return (x + w <= qr_img.shape[1] and y + h <= qr_img.shape[0])

# def blend_edges_with_qr(qr_img, embed_img, x, y, module_size, blend_percent):
#     blend_mask = np.zeros(embed_img.shape[:2], dtype=np.float32)
#     border_width = module_size * 2
#     scale_alpha = np.clip(blend_percent / 100.0, 0.0, 1.0)

#     h, w = embed_img.shape[:2]

#     for i in range(h):
#         for j in range(w):
#             top_alpha = 1.0 - min(i, border_width) / border_width
#             bottom_alpha = 1.0 - min(h - 1 - i, border_width) / border_width
#             left_alpha = 1.0 - min(j, border_width) / border_width
#             right_alpha = 1.0 - min(w - 1 - j, border_width) / border_width
#             blend_mask[i, j] = max(top_alpha, bottom_alpha, left_alpha, right_alpha) * scale_alpha

#     roi = qr_img[y:y+h, x:x+w].astype(np.float32)
#     embed = embed_img.astype(np.float32)

#     if embed.shape[2] == 4:
#         alpha = embed[:, :, 3] / 255.0
#         for c in range(3):
#             roi[:, :, c] = (blend_mask * alpha * embed[:, :, c] + (1 - blend_mask * alpha) * roi[:, :, c])
#     else:
#         for c in range(3):
#             roi[:, :, c] = (blend_mask * embed[:, :, c] + (1 - blend_mask) * roi[:, :, c])

#     qr_img[y:y+h, x:x+w] = np.clip(roi, 0, 255).astype(np.uint8)

# def embed_image(qr_path, embed_path, output_path, blend_percent, seed=''):
#     qr_img = cv2.imread(qr_path, cv2.IMREAD_COLOR)
#     embed_img = cv2.imread(embed_path, cv2.IMREAD_UNCHANGED)

#     if qr_img is None or embed_img is None:
#         print("Failed to read input images.")
#         return

#     module_size = max(1, qr_img.shape[1] // 21)

#     max_dim = min(qr_img.shape[:2]) // 3
#     h, w = embed_img.shape[:2]
#     scale = min(max_dim / h, max_dim / w, 1.0)
#     embed_img = cv2.resize(embed_img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)

#     w, h = embed_img.shape[1], embed_img.shape[0]

#     hash_val = int(hashlib.sha256((seed or str(random.random())).encode()).hexdigest(), 16)
#     rng_x = random.Random(hash_val)
#     rng_y = random.Random(hash_val ^ 0x55555555)

#     for _ in range(100):
#         x = rng_x.randint(0, qr_img.shape[1] - w)
#         y = rng_y.randint(0, qr_img.shape[0] - h)
#         if is_safe_zone(qr_img, x, y, w, h, module_size):
#             break
#     else:
#         x = min(qr_img.shape[1] - w, max(0, x))
#         y = min(qr_img.shape[0] - h, max(0, y))

#     blend_edges_with_qr(qr_img, embed_img, x, y, module_size, blend_percent)
#     cv2.imwrite(output_path, qr_img)
#     print(f"Saved embedded image at {output_path}")

# # Example usage
# if __name__ == "__main__":
#     import sys
#     if len(sys.argv) < 6:
#         print("Usage: python embed.py <qrPath> <embedPath> <outputPath> <seed> <blendPercent>")
#     else:
#         embed_image(sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[5]), sys.argv[4] )

import cv2
import numpy as np
import random

def is_safe_zone(qr_img, x, y, w, h, module_size):
    finder_size = 7 * module_size
    quiet_zone = 4 * module_size

    if ((x < finder_size + quiet_zone and y < finder_size + quiet_zone) or
        (x > qr_img.shape[1] - finder_size - quiet_zone and y < finder_size + quiet_zone) or
        (x < finder_size + quiet_zone and y > qr_img.shape[0] - finder_size - quiet_zone)):
        return False

    timing_pos = finder_size + quiet_zone - module_size // 2
    if abs(y - timing_pos) < module_size // 2 + 1 or abs(x - timing_pos) < module_size // 2 + 1:
        return False

    return (x + w <= qr_img.shape[1] and y + h <= qr_img.shape[0])

def blend_edges_with_qr(qr_img, embed_img, x, y, module_size, blend_percent):
    border_width = module_size * 2
    # scale_alpha = max(0, min(100, blend_percent)) / 100.0  # C++-style clamping
    scale_alpha = np.clip(blend_percent / 100.0, 0.0, 1.0)
    
    # C++-style color sampling
    top_color = np.mean(qr_img[max(0,y-1):y, x:x+embed_img.shape[1]], axis=(0,1))
    bottom_color = np.mean(qr_img[min(qr_img.shape[0]-1,y+embed_img.shape[0]):y+embed_img.shape[0]+1, x:x+embed_img.shape[1]], axis=(0,1))
    left_color = np.mean(qr_img[y:y+embed_img.shape[0], max(0,x-1):x], axis=(0,1))
    right_color = np.mean(qr_img[y:y+embed_img.shape[0], min(qr_img.shape[1]-1,x+embed_img.shape[1]):x+embed_img.shape[1]+1], axis=(0,1))
    
    target_color = (top_color + bottom_color + left_color + right_color) / 4  # C++ averaging

    blend_mask = np.zeros(embed_img.shape[:2], dtype=np.float32)
    h, w = embed_img.shape[:2]

    for i in range(h):
        for j in range(w):
            top_alpha = 1.0 - min(i, border_width) / border_width
            bottom_alpha = 1.0 - min(h-1-i, border_width) / border_width
            left_alpha = 1.0 - min(j, border_width) / border_width
            right_alpha = 1.0 - min(w-1-j, border_width) / border_width
            blend_mask[i,j] = max(top_alpha, bottom_alpha, left_alpha, right_alpha) * scale_alpha

    roi = qr_img[y:y+h, x:x+w].astype(np.float32)
    embed = embed_img.astype(np.float32)

    if embed.shape[2] == 4:
        alpha = embed[:, :, 3] / 255.0
        for c in range(3):
            # C++-style blending with target_color
            # roi[:, :, c] = blend_mask * alpha * embed[:, :, c] + (1 - blend_mask * alpha) * target_color[c]
            roi[:, :, c] = ((1 - blend_mask) * alpha * embed[:, :, c] + blend_mask * target_color[c])
    else:
        for c in range(3):
            # roi[:, :, c] = blend_mask * embed[:, :, c] + (1 - blend_mask) * target_color[c]
            roi[:, :, c] = ((1 - blend_mask) * embed[:, :, c] + blend_mask * target_color[c])

    qr_img[y:y+h, x:x+w] = np.clip(roi, 0, 255).astype(np.uint8)

def embed_image(qr_path, embed_path, output_path, blend_percent, seed=''):
    qr_img = cv2.imread(qr_path, cv2.IMREAD_COLOR)
    embed_img = cv2.imread(embed_path, cv2.IMREAD_UNCHANGED)

    if qr_img is None or embed_img is None:
        print("Failed to read input images.")
        return

    module_size = max(1, qr_img.shape[1] / 21)  # Match C++ integer division

    max_dim = min(qr_img.shape[:2]) // 3
    h, w = embed_img.shape[:2]
    scale = min(max_dim / h, max_dim / w, 1.0)
    embed_img = cv2.resize(embed_img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)

    w, h = embed_img.shape[1], embed_img.shape[0]

    # C++-style RNG initialization
    combined_seed = str(random.random()) + seed
    seed_hash = 0
    for c in combined_seed:
        seed_hash = (seed_hash << 5) + seed_hash + ord(c)  # Identical to C++

    rng_x = random.Random(seed_hash)
    rng_y = random.Random(seed_hash ^ 0x55555555)  # Same XOR pattern

    for _ in range(100):
        x = rng_x.randint(0, qr_img.shape[1] - w)
        y = rng_y.randint(0, qr_img.shape[0] - h)
        if is_safe_zone(qr_img, x, y, w, h, module_size):
            break
    else:
        x = min(qr_img.shape[1] - w, max(0, x))
        y = min(qr_img.shape[0] - h, max(0, y))

    blend_edges_with_qr(qr_img, embed_img, x, y, module_size, blend_percent)
    cv2.imwrite(output_path, qr_img)
    print(f"Saved embedded image at {output_path}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 6:
        print("Usage: python embed.py <qrPath> <embedPath> <outputPath> <seed> <blendPercent>")
    else:
        blend_percent = max(0, min(100, int(sys.argv[5])))  # C++-style clamping
        embed_image(sys.argv[1], sys.argv[2], sys.argv[3], blend_percent, sys.argv[4])
