import pygame
import numpy as np
from scipy.ndimage import gaussian_filter

class GaussianBlur:
    def __init__(self, kernelsize=7):
        self.kernel_size = kernelsize

    def filter(self, srfc, xpos, ypos, width, height):
        # Get subsurface area to blur
        sub_surface = srfc.subsurface((xpos, ypos, width, height))
        array3d = pygame.surfarray.array3d(sub_surface)  # shape: (width, height, 3)

        # Transpose to shape (height, width, 3) for filtering
        array3d = np.transpose(array3d, (1, 0, 2))

        # Apply Gaussian blur
        blurred = gaussian_filter(array3d, sigma=(self.kernel_size, self.kernel_size, 0))

        # Transpose back to (width, height, 3) for pygame
        blurred = np.transpose(blurred, (1, 0, 2))

        # Ensure data type and shape match
        blurred = np.ascontiguousarray(blurred.astype(np.uint8))

        # Create new surface and blit the blurred array
        nSrfc = pygame.Surface((width, height))
        pygame.surfarray.blit_array(nSrfc, blurred)

        return nSrfc
