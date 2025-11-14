"""
In-memory store for geo features.
"""
import secrets
from typing import Optional, Dict, List, Any


class State:
    """
    Manages the in-memory state of all geographic features.
    
    Features are stored by ID with their type, coordinates, and parameters.
    """
    
    def __init__(self):
        self.features: Dict[str, Dict[str, Any]] = {}
        self.used_ids: set = set()
    
    def add_feature(self, feature_type: str, coords: List[List[float]], 
                   params: Dict[str, str], feature_id: Optional[str] = None) -> str:
        """
        Add a feature to the state.
        
        Args:
            feature_type: Type of feature ('point', 'polyline', 'polygon')
            coords: List of [lat, lng] coordinate pairs
            params: Dictionary of feature parameters
            feature_id: Optional user-defined ID. If None, generates random ID.
        
        Returns:
            The ID of the added feature (user-provided or generated)
        
        Raises:
            ValueError: If the provided ID already exists
        """
        if feature_id is None:
            feature_id = self._generate_id()
        else:
            if feature_id in self.used_ids:
                raise ValueError(f"Feature ID '{feature_id}' already exists")
        
        self.features[feature_id] = {
            'type': feature_type,
            'coords': coords,
            'params': params
        }
        self.used_ids.add(feature_id)
        
        return feature_id
    
    def get_feature(self, feature_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a feature by ID.
        
        Args:
            feature_id: The ID of the feature to retrieve
        
        Returns:
            The feature dict or None if not found
        """
        return self.features.get(feature_id)
    
    def remove_feature(self, feature_id: str) -> bool:
        """
        Remove a feature by ID.
        
        Args:
            feature_id: The ID of the feature to remove
        
        Returns:
            True if the feature was removed, False if it didn't exist
        """
        if feature_id in self.features:
            del self.features[feature_id]
            self.used_ids.discard(feature_id)
            return True
        return False
    
    def remove_features_by_tag(self, tag: str) -> List[str]:
        """
        Remove all features with the specified tag.
        
        Args:
            tag: The tag to match
        
        Returns:
            List of IDs that were removed
        """
        removed_ids = []
        for feature_id, feature_data in list(self.features.items()):
            if feature_data['params'].get('tag') == tag:
                del self.features[feature_id]
                self.used_ids.discard(feature_id)
                removed_ids.append(feature_id)
        return removed_ids
    
    def clear_all(self) -> List[str]:
        """
        Remove all features from the state.
        
        Returns:
            List of IDs that were removed
        """
        removed_ids = list(self.features.keys())
        self.features.clear()
        self.used_ids.clear()
        return removed_ids
    
    def _generate_id(self) -> str:
        """
        Generate a random unique ID (8-character hex).
        
        Returns:
            A unique random ID
        """
        while True:
            new_id = secrets.token_hex(4)  # 4 bytes = 8 hex chars
            if new_id not in self.used_ids:
                return new_id
