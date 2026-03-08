"""
Base class for all signal cells implementing common patterns
"""
import logging
import threading
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime

from core.firebase_nexus import FirebaseNexus, SignalPacket


class BaseCell(ABC):
    """
    Abstract base class for all signal processing cells
    
    Implements:
    - Thread-safe operation
    - Firestore communication
    - Error handling and recovery
    - Health monitoring
    - Graceful shutdown
    """
    
    def __init__(self, cell_type: str, config: Dict[str, Any] = None):
        """
        Initialize the cell
        
        Args:
            cell_type: Unique identifier for this cell type
            config: Configuration dictionary
        """
        self.cell_type = cell_type
        self.config = config or {}
        
        # Initialize components
        self.nexus = FirebaseNexus()
        self.logger = logging.getLogger(f"cell.{cell_type}")
        
        # State management
        self._running = False
        self._thread = None
        self._last_cycle_time = None
        self._error_count = 0
        self._max_errors = self.config.get('max_errors', 10)
        
        # Performance tracking
        self.cycles_completed = 0
        self.total_processing_time = 0
        
        # Cell-specific state
        self._state = {}
        
        self.logger.info(f"Cell {cell_type} initialized")
    
    def start(self):
        """Start the cell's processing thread"""
        if self._running:
            self.logger.warning("Cell already running")
            return
            
        self._running = True
        self._thread = threading.Thread(
            target=self._run_loop,
            name=f"cell_{self.cell_type}",
            daemon=True
        )
        self._thread.start()
        
        self.logger.info(f"Cell {self.cell_type} started")
    
    def stop(self):
        """Stop the cell gracefully"""
        self._running = False
        
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=30)  # Wait up to 30 seconds
            
        self.logger.info(f"Cell {self.cell_type} stopped")
    
    def _run_loop(self):
        """Main processing loop with error handling"""
        cycle_interval = self.config.get('cycle_interval', 60)  # seconds
        
        while self._running: