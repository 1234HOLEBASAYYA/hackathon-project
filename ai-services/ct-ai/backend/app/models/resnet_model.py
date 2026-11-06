import torch
import torch.nn as nn
import torchvision.models as models


def create_resnet18_classifier(num_classes=2, dropout_p=0.3):
    """
    Constructs ResNet18 model matching the exact architecture used in training.
    """
    model = models.resnet18(weights=None)
    in_features = model.fc.in_features
    model.fc = nn.Sequential(
        nn.Dropout(p=dropout_p),
        nn.Linear(in_features, num_classes)
    )
    return model


def load_model(weights_path: str, device: torch.device = None):
    """
    Loads the trained ResNet18 weights into memory.
    """
    if device is None:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    model = create_resnet18_classifier(num_classes=2)
    state_dict = torch.load(weights_path, map_location=device)
    model.load_state_dict(state_dict)
    model.to(device)
    model.eval()
    return model
