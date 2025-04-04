import torch
from torch.utils.data import Dataset, DataLoader, random_split
import numpy as np
import os
from PIL import Image
import torchvision.transforms as transforms

class GuitarTabDataset(Dataset):
    def __init__(self, audio_dir, annotation_dir):
        self.audio_files = sorted([f for f in os.listdir(audio_dir) if f.endswith('.png')])
        self.annotation_files = sorted([f for f in os.listdir(annotation_dir) if f.endswith('.npy')])

        assert len(self.audio_files) == len(self.annotation_files), "Mismatch in audio and annotation file counts."

        self.audio_dir = audio_dir
        self.annotation_dir = annotation_dir
        self.transform = transforms.Compose([
        transforms.Resize((224, 224)),  # Resize to ResNet input size
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])  # ImageNet normalization
         ])

    def __len__(self):
        return len(self.audio_files)

    def __getitem__(self, idx):
        # Load spectrogram image
        audio_path = os.path.join(self.audio_dir, self.audio_files[idx])
        audio = Image.open(audio_path).convert("RGB")
        audio = self.transform(audio)  # Shape: (3, H, W)
    
        # Load annotation file
        annotation_path = os.path.join(self.annotation_dir, self.annotation_files[idx])
        annotation = np.load(annotation_path, mmap_mode='r')
        
        # Check the shape of the annotation
        # print(f"Raw annotation shape: {annotation.shape}")
        
        # If it's one-hot encoded, convert it to class indices
        if len(annotation.shape) == 2 and annotation.shape[1] == 19:
            annotation = np.argmax(annotation, axis=1)
        
        # Convert to tensor
        annotation = torch.tensor(annotation, dtype=torch.long)
        
        # Ensure annotation has the expected shape
        if annotation.shape[0] != 6:
            print(f"Warning: Annotation has unexpected shape: {annotation.shape}")
        
        return audio, annotation
    
def create_dataloaders(audio_dir, annotation_dir, batch_size=64, train_ratio=0.8, val_ratio=0.1):
    dataset = GuitarTabDataset(audio_dir, annotation_dir)

    # Split dataset into training, validation, and testing
    train_size = int(train_ratio * len(dataset))
    val_size = int(val_ratio * len(dataset))
    test_size = len(dataset) - train_size - val_size

    train_dataset, val_dataset, test_dataset = random_split(dataset, [train_size, val_size, test_size])

    loader_args = {
        'batch_size': batch_size,
        'num_workers': min(4, os.cpu_count() // 2),  # Safer num_workers
        'pin_memory': True,  
    }

    train_loader = DataLoader(train_dataset, shuffle=True, **loader_args)
    val_loader = DataLoader(val_dataset, shuffle=False, **loader_args)
    test_loader = DataLoader(test_dataset, shuffle=False, **loader_args)

    return train_loader, val_loader, test_loader
