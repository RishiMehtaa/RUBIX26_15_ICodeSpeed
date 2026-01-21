"""
Shared Frame Buffer using Memory-Mapped File
Allows zero-copy frame sharing between Python and Node.js/Electron
"""

import mmap
import struct
import logging
import cv2
import time
import os


class SharedFrameBuffer:
    """
    Shared memory buffer for video frames using memory-mapped file
    
    Format:
    [4 bytes: frame_width]
    [4 bytes: frame_height]
    [4 bytes: channels (3 for BGR)]
    [4 bytes: timestamp_sec]
    [4 bytes: timestamp_usec]
    [4 bytes: frame_size]
    [remaining: frame_data (raw BGR bytes)]
    """
    
    HEADER_SIZE = 24  # 6 * 4 bytes
    MAX_FRAME_SIZE = 1920 * 1080 * 3  # Max HD frame
    TOTAL_SIZE = HEADER_SIZE + MAX_FRAME_SIZE
    
    def __init__(self, file_path, create=True):
        """
        Initialize shared frame buffer
        
        Args:
            file_path: Full path to memory-mapped file
            create: If True, create new buffer; if False, open existing
        """
        self.file_path = file_path
        self.logger = logging.getLogger(self.__class__.__name__)
        self.mmap_file = None
        self.file_handle = None
        
        if create:
            self._create_buffer()
        else:
            self._open_buffer()
    
    def _create_buffer(self):
        """Create new shared memory buffer"""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
            
            # Create file with required size
            with open(self.file_path, 'wb') as f:
                f.write(b'\x00' * self.TOTAL_SIZE)
            
            # Open for reading and writing
            self.file_handle = open(self.file_path, 'r+b')
            self.mmap_file = mmap.mmap(
                self.file_handle.fileno(),
                self.TOTAL_SIZE,
                access=mmap.ACCESS_WRITE
            )
            
            # Initialize header with zeros
            self.mmap_file.seek(0)
            self.mmap_file.write(struct.pack('6I', 0, 0, 0, 0, 0, 0))
            
            self.logger.info(f"Created shared buffer at: {self.file_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to create shared buffer: {e}")
            raise
    
    def _open_buffer(self):
        """Open existing shared memory buffer"""
        try:
            self.file_handle = open(self.file_path, 'r+b')
            self.mmap_file = mmap.mmap(
                self.file_handle.fileno(),
                self.TOTAL_SIZE,
                access=mmap.ACCESS_READ
            )
            self.logger.info(f"Opened shared buffer at: {self.file_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to open shared buffer: {e}")
            raise
    
    def write_frame(self, frame):
        """
        Write frame to shared memory
        
        Args:
            frame: OpenCV frame (BGR format)
        
        Returns:
            bool: Success status
        """
        if self.mmap_file is None:
            return False
        
        try:
            height, width, channels = frame.shape
            frame_size = frame.size
            
            # Check size limit
            if frame_size > self.MAX_FRAME_SIZE:
                self.logger.warning(f"Frame too large: {frame_size} > {self.MAX_FRAME_SIZE}")
                return False
            
            # Get timestamp
            timestamp = time.time()
            timestamp_sec = int(timestamp)
            timestamp_usec = int((timestamp - timestamp_sec) * 1_000_000)
            
            # Write header
            self.mmap_file.seek(0)
            header = struct.pack(
                '6I',
                width,
                height,
                channels,
                timestamp_sec,
                timestamp_usec,
                frame_size
            )
            self.mmap_file.write(header)
            
            # Write frame data (raw bytes)
            self.mmap_file.write(frame.tobytes())
            self.mmap_file.flush()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error writing frame: {e}")
            return False
    
    def read_frame(self):
        """
        Read frame from shared memory
        
        Returns:
            tuple: (frame, timestamp) or (None, None) on error
        """
        if self.mmap_file is None:
            return None, None
        
        try:
            # Read header
            self.mmap_file.seek(0)
            header_data = self.mmap_file.read(self.HEADER_SIZE)
            width, height, channels, ts_sec, ts_usec, frame_size = struct.unpack('6I', header_data)
            
            # Check if valid frame
            if width == 0 or height == 0 or frame_size == 0:
                return None, None
            
            # Read frame data
            frame_data = self.mmap_file.read(frame_size)
            
            # Reconstruct frame
            import numpy as np
            frame = np.frombuffer(frame_data, dtype=np.uint8).reshape((height, width, channels))
            
            # Reconstruct timestamp
            timestamp = ts_sec + (ts_usec / 1_000_000)
            
            return frame, timestamp
            
        except Exception as e:
            self.logger.error(f"Error reading frame: {e}")
            return None, None
    
    def read_frame_info(self):
        """
        Read only frame metadata (no frame data)
        
        Returns:
            dict: Frame info or None on error
        """
        if self.mmap_file is None:
            return None
        
        try:
            self.mmap_file.seek(0)
            header_data = self.mmap_file.read(self.HEADER_SIZE)
            width, height, channels, ts_sec, ts_usec, frame_size = struct.unpack('6I', header_data)
            
            if width == 0 or height == 0:
                return None
            
            return {
                'width': width,
                'height': height,
                'channels': channels,
                'timestamp': ts_sec + (ts_usec / 1_000_000),
                'frame_size': frame_size
            }
            
        except Exception as e:
            self.logger.error(f"Error reading frame info: {e}")
            return None
    
    def close(self):
        """Close shared memory buffer"""
        try:
            if self.mmap_file:
                self.mmap_file.close()
            if self.file_handle:
                self.file_handle.close()
            self.logger.info("Closed shared buffer")
        except Exception as e:
            self.logger.error(f"Error closing buffer: {e}")
    
    def cleanup(self):
        """Close and delete buffer file"""
        self.close()
        try:
            if os.path.exists(self.file_path):
                os.remove(self.file_path)
                self.logger.info(f"Deleted buffer file: {self.file_path}")
        except Exception as e:
            self.logger.error(f"Error deleting buffer file: {e}")
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
