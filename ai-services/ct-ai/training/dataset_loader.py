import os
import torch
from torch.utils.data import DataLoader, Dataset, WeightedRandomSampler
from torchvision.datasets import ImageFolder
from PIL import Image

try:
    from training.config import (
        TRAIN_DIR, VAL_DIR, TEST_DIR, BATCH_SIZE, NUM_WORKERS,
        CLASS_NAMES, CLASS_TO_IDX
    )
    from training.preprocessing import get_train_transforms, get_eval_transforms, EnsureRGB
except ImportError:
    from config import (
        TRAIN_DIR, VAL_DIR, TEST_DIR, BATCH_SIZE, NUM_WORKERS,
        CLASS_NAMES, CLASS_TO_IDX
    )
    from preprocessing import get_train_transforms, get_eval_transforms, EnsureRGB


class SafeImageFolder(Dataset):
    """
    Robust Dataset loader that ensures RGB conversion and tracks sample paths.
    """
    def __init__(self, root_dir, transform=None):
        self.root_dir = str(root_dir)
        self.transform = transform
        self.samples = []
        self.classes = CLASS_NAMES
        self.class_to_idx = CLASS_TO_IDX

        for class_name, class_idx in self.class_to_idx.items():
            class_dir = os.path.join(self.root_dir, class_name)
            if not os.path.exists(class_dir):
                continue
            for fname in os.listdir(class_dir):
                if fname.lower().endswith((".png", ".jpg", ".jpeg")):
                    fpath = os.path.join(class_dir, fname)
                    self.samples.append((fpath, class_idx))

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        path, label = self.samples[idx]
        with Image.open(path) as img:
            img = EnsureRGB()(img)
            if self.transform:
                img = self.transform(img)
        return img, label

    def get_class_counts(self):
        counts = {c: 0 for c in self.classes}
        for _, label in self.samples:
            class_name = self.classes[label]
            counts[class_name] += 1
        return counts


def get_dataloaders(batch_size=BATCH_SIZE, num_workers=NUM_WORKERS, use_balanced_sampler=True):
    """
    Builds data loaders for train, val, and test splits.
    Uses WeightedRandomSampler to present an equal 50/50 balance of NORMAL
    and PNEUMONIA cases per training batch to eliminate majority-class bias.
    """
    train_dataset = SafeImageFolder(TRAIN_DIR, transform=get_train_transforms())
    val_dataset = SafeImageFolder(VAL_DIR, transform=get_eval_transforms())
    test_dataset = SafeImageFolder(TEST_DIR, transform=get_eval_transforms())

    train_counts = train_dataset.get_class_counts()
    total_samples = len(train_dataset)
    num_classes = len(CLASS_NAMES)
    
    # Weight per class = total / (num_classes * count)
    weights = [
        total_samples / (num_classes * max(1, train_counts[cls]))
        for cls in CLASS_NAMES
    ]
    class_weights = torch.FloatTensor(weights)

    if use_balanced_sampler:
        # Per-sample weight for equal batch distribution
        sample_weights = [weights[label] for _, label in train_dataset.samples]
        sampler = WeightedRandomSampler(
            weights=sample_weights,
            num_samples=len(sample_weights),
            replacement=True
        )
        train_loader = DataLoader(
            train_dataset,
            batch_size=batch_size,
            sampler=sampler,
            num_workers=num_workers,
            pin_memory=torch.cuda.is_available()
        )
    else:
        train_loader = DataLoader(
            train_dataset,
            batch_size=batch_size,
            shuffle=True,
            num_workers=num_workers,
            pin_memory=torch.cuda.is_available()
        )

    val_loader = DataLoader(
        val_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=torch.cuda.is_available()
    )

    test_loader = DataLoader(
        test_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=torch.cuda.is_available()
    )

    return train_loader, val_loader, test_loader, class_weights, train_dataset, val_dataset, test_dataset
