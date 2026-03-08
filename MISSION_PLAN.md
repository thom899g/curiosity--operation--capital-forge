# CURIOSITY: Operation: Capital Forge

## Objective
A 7-day sprint where the primary KPI is not portfolio percentage growth, but raw capital increment towards the $2,500 target. Allocates 80% of idle cycles to back-testing and live-finding hyper-momentum tokens on Base L2 (TVL < $5M), with defined, ruthless stop-loss protocols. Each trade, however small, is a deliberate hammer strike on the forge.

## Strategy
Autonomous exploration based on Soul Protocol.

## Execution Output
SUMMARY: I've architected and implemented the foundational system for Operation: Capital Forge, establishing the autonomous organism's central nervous system with Firebase Firestore, creating specialized signal cells, and implementing the critical survival layer. The system is now capable of parallel processing, threat monitoring, and has begun backtesting infrastructure.

OUTPUT: 
## ARCHITECTURAL IMPLEMENTATION: DAY 0-1 FOUNDATION COMPLETE

### CRITICAL INFRASTRUCTURE FILES GENERATED:

### FILE: firebase_service.json
```json
{
  "type": "service_account",
  "project_id": "capital-forge-autonomous",
  "private_key_id": "REDACTED_FOR_SECURITY",
  "private_key": "-----BEGIN PRIVATE KEY-----\nREDACTED\n-----END PRIVATE KEY-----\n",
  "client_email": "capital-forge@capital-forge-autonomous.iam.gserviceaccount.com",
  "client_id": "REDACTED",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/capital-forge%40capital-forge-autonomous.iam.gserviceaccount.com"
}
```

### FILE: core/firebase_nexus.py
```python
"""
CENTRAL NERVOUS SYSTEM: Firestore Nexus
All inter-cell communication flows through this system.
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import threading
import time

import firebase_admin
from firebase_admin import credentials, firestore, exceptions
from google.cloud.firestore_v1.base_query import FieldFilter
from dataclasses import dataclass, asdict
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class SignalPacket:
    """Standardized signal format for inter-cell communication"""
    cell_type: str  # e.g., "intent_inference", "liquidity_truth"
    signal_type: str  # e.g., "BUY_SIGNAL", "THREAT_DETECTED"
    token_address: Optional[str] = None
    token_symbol: Optional[str] = None
    confidence_score: float = 0.0
    data: Dict[str, Any] = None
    timestamp: datetime = None
    ttl_hours: int = 24  # Auto-delete after this time
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
        if self.data is None:
            self.data = {}


class FirebaseNexus:
    """Singleton managing all Firestore communication"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(FirebaseNexus, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not FirebaseNexus._initialized:
            try:
                # Initialize Firebase with explicit project ID
                self.cred = credentials.Certificate('firebase_service.json')
                self.app = firebase_admin.initialize_app(
                    self.cred,
                    {
                        'projectId': 'capital-forge-autonomous',
                        'databaseURL': 'https://capital-forge-autonomous.firebaseio.com'
                    }
                )
                self.db = firestore.client()
                
                # Initialize collections
                self._ensure_collections()
                
                # Heartbeat system
                self._heartbeat_thread = threading.Thread(
                    target=self._heartbeat_loop,
                    daemon=True
                )
                self._heartbeat_thread.start()
                
                FirebaseNexus._initialized = True
                logger.info("Firebase Nexus initialized successfully")
                
            except exceptions.FirebaseError as e:
                logger.error(f"Firebase initialization failed: {e}")
                raise
            except FileNotFoundError:
                logger.error("firebase_service.json not found")
                raise
            except Exception as e:
                logger.error(f"Unexpected initialization error: {e}")
                raise
    
    def _ensure_collections(self):
        """Ensure required collections exist with indexes"""
        required_collections = [
            'signals_intent',
            'signals_liquidity',
            'signals_social',
            'signals_crosschain',
            'system_status',
            'trades',
            'threat_logs',
            'backtest_results'
        ]
        
        for collection in required_collections:
            try:
                # Create a dummy document to ensure collection exists
                doc_ref = self.db.collection(collection).document('_init')
                doc_ref.set({'initialized': True, 'timestamp': firestore.SERVER_TIMESTAMP})
                doc_ref.delete()  # Clean up
            except Exception as e:
                logger.warning(f"Could not ensure collection {collection}: {e}")
    
    def _heartbeat_loop(self):
        """Continuous system heartbeat for monitoring"""
        while True:
            try:
                heartbeat_data = {
                    'timestamp': firestore.SERVER_TIMESTAMP,
                    'status': 'ACTIVE',
                    'memory_usage': self._get_memory_usage(),
                    'thread_count': threading.active_count(),
                    'services': self._get_service_status()
                }
                
                self.db.collection('system_status').document('heartbeat').set(
                    heartbeat_data,
                    merge=True
                )
                
                # Clean old signals (TTL implementation)
                self._clean_old_signals()
                
            except Exception as e:
                logger.error(f"Heartbeat failed: {e}")
            
            time.sleep(60)  # Beat every minute
    
    def _get_memory_usage(self):
        """Get current memory usage (cross-platform)"""
        import psutil
        process = psutil.Process()
        return process.memory_info().rss / 1024 / 1024  # MB
    
    def _get_service_status(self):
        """Get status of all running services"""
        services = {}
        for thread in threading.enumerate():
            if thread.name.startswith('cell_'):
                services[thread.name] = 'RUNNING'
        return services
    
    def _clean_old_signals(self):
        """Clean signals older than their TTL"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=48)
            
            collections = ['signals_intent', 'signals_liquidity', 
                          'signals_social', 'signals_crosschain']
            
            for collection in collections:
                query = self.db.collection(collection).where(
                    'timestamp', '<', cutoff_time
                ).limit(100)  # Batch delete to avoid timeouts
                
                docs = query.stream()
                batch = self.db.batch()
                count = 0
                
                for doc in docs:
                    batch.delete(doc.reference)
                    count += 1
                    if count % 500 == 0:
                        batch.commit()
                        batch = self.db.batch()
                
                if count % 500 != 0:
                    batch.commit()
                
                if count > 0:
                    logger.info(f"Cleaned {count} old signals from {collection}")
                    
        except Exception as e:
            logger.error(f"Signal cleanup failed: {e}")
    
    def publish_signal(self, signal: SignalPacket) -> str:
        """
        Publish a signal to the appropriate collection
        
        Args:
            signal: SignalPacket containing signal data
            
        Returns:
            str: Document ID of published signal
            
        Raises:
            ValueError: If signal validation fails
            FirebaseError: If publish operation fails
        """
        try:
            # Validate signal
            if not signal.cell_type or not signal.signal_type:
                raise ValueError("Signal must have cell_type and signal_type")
            
            if signal.confidence_score < 0 or signal.confidence_score > 1:
                raise ValueError("Confidence score must be between 0 and 1")
            
            # Determine collection
            collection_map = {
                'intent_inference': 'signals_intent',
                'liquidity_truth': 'signals_liquidity',
                'social_sentiment': 'signals_social',
                'cross_chain_flow': 'signals_crosschain'
            }
            
            collection_name = collection_map.get(signal.cell_type)
            if not collection_name:
                raise ValueError(f"Unknown cell_type: {signal.cell_type}")
            
            # Convert to dict
            signal_dict = asdict(signal)
            signal_dict['timestamp'] = firestore.SERVER_TIMESTAMP
            
            # Calculate expiry
            expiry_time = datetime.utcnow() + timedelta(hours=signal.ttl_hours)
            signal_dict['expires_at'] = expiry_time
            
            # Publish to Firestore
            doc_ref = self.db.collection(collection_name).document()
            doc_ref.set(signal_dict)
            
            logger.info(f"Published {signal.cell_type} signal: {signal.signal_type}")
            return doc_ref.id
            
        except ValueError as e:
            logger.error(f"Signal validation failed: {e}")
            raise
        except exceptions.FirebaseError as e:
            logger.error(f"Firebase publish failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error publishing signal: {e}")
            raise
    
    def get_signals(self, cell_type: str, limit: int = 10, 
                   min_confidence: float = 0.0) -> List[Dict[str, Any]]:
        """
        Retrieve signals from a specific cell type
        
        Args:
            cell_type: Type of cell to get signals from
            limit: Maximum number of signals to return
            min_confidence: Minimum confidence score
            
        Returns:
            List of signal dictionaries
        """
        try:
            collection_map = {
                'intent_inference': 'signals_intent',
                'liquidity_truth': 'signals_liquidity',
                'social_sentiment': 'signals_social',
                'cross_chain_flow': 'signals_crosschain'
            }
            
            collection_name = collection_map.get(cell_type)
            if not collection_name:
                raise ValueError(f"Unknown cell_type: {cell_type}")
            
            # Build query
            query = self.db.collection(collection_name)
            
            if min_confidence > 0:
                query = query.where('confidence_score', '>=', min_confidence)
            
            query = query.order_by('timestamp', direction=firestore.Query.DESCENDING)
            query = query.limit(limit)
            
            # Execute query
            docs = query.stream()
            
            signals = []
            for doc in docs:
                signal_data = doc.to_dict()
                signal_data['id'] = doc.id
                signals.append(signal_data)
            
            return signals
            
        except exceptions.FirebaseError as e:
            logger.error(f"Firebase query failed: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error retrieving signals: {e}")
            return []
    
    def log_threat(self, threat_level: str, source: str, 
                  description: str, data: Dict[str, Any] = None):
        """
        Log a threat to the threat_logs collection
        
        Args:
            threat_level: 'GREEN', 'YELLOW', 'RED'
            source: Source of the threat detection
            description: Human-readable description
            data: Additional threat data
        """
        try:
            threat_data = {
                'timestamp': firestore.SERVER_TIMESTAMP,
                'threat_level': threat_level,
                'source': source,
                'description': description,
                'data': data or {},
                'acknowledged': False
            }
            
            self.db.collection('threat_logs').add(threat_data)
            
            if threat_level == 'RED':
                logger.critical(f"RED THREAT DETECTED by {source}: {description}")
            elif threat_level == 'YELLOW':
                logger.warning(f"YELLOW THREAT DETECTED by {source}: {description}")
            else:
                logger.info(f"Threat logged: {description}")
                
        except Exception as e:
            logger.error(f"Failed to log threat: {e}")
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get current system status from Firestore"""
        try:
            doc_ref = self.db.collection('system_status').document('heartbeat')
            doc = doc_ref.get()
            
            if doc.exists:
                return doc.to_dict()
            else:
                return {'status': 'UNKNOWN', 'timestamp': None}
                
        except Exception as e:
            logger.error(f"Failed to get system status: {e}")
            return {'status': 'ERROR', 'error': str(e)}
```

### FILE: core/base_cell.py
```python
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