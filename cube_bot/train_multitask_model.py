import torch
import torch.nn as nn
import torch.nn.functional as F

class MultiTaskLineAndLetterCNN(nn.Module):
    def __init__(self):
        super(MultiTaskLineAndLetterCNN, self).__init__()
        
        # --- Shared Feature Extractor ---
        # Input image shape: (3, 120, 160)
        self.conv1 = nn.Conv2d(3, 16, kernel_size=5, stride=2, padding=2)  # Shape: (16, 60, 80)
        self.conv2 = nn.Conv2d(16, 32, kernel_size=3, stride=2, padding=1) # Shape: (32, 30, 40)
        self.conv3 = nn.Conv2d(32, 64, kernel_size=3, stride=2, padding=1) # Shape: (64, 15, 20)
        
        self.fc_shared = nn.Linear(64 * 15 * 20, 256)

        # --- Head 1: Continuous Error Estimation (Regression) ---
        # Outputs a single float value (e.g., -1.0 for hard left, 1.0 for hard right)
        self.error_head = nn.Linear(256, 1)

        # --- Head 2: Letter Recognition (Classification) ---
        # 4 classes: 0 = "None", 1 = "A", 2 = "B", 3 = "C"
        self.letter_head = nn.Linear(256, 4)

    def forward(self, x):
        # Extract features through convolutions
        x = F.relu(self.conv1(x))
        x = F.relu(self.conv2(x))
        x = F.relu(self.conv3(x))
        
        # Flatten and pass to shared fully connected layer
        x = x.view(-1, 64 * 15 * 20)
        shared = F.relu(self.fc_shared(x))
        
        # Separate the tracks
        raw_error = self.error_head(shared)          # Shape: (batch, 1)
        letter_logits = self.letter_head(shared)      # Shape: (batch, 4)
        
        return raw_error, letter_logits

# --- Loss Function Concept for Training ---
# If you are training this, remember you must use two different loss functions:
# criterion_error = nn.MSELoss()                      # For the continuous number
# criterion_letter = nn.CrossEntropyLoss()            # For the categorical letter
# total_loss = error_loss + (letter_loss * weight)
