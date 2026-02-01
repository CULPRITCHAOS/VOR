"""Trainer for VQ codebooks using synthetic data."""
from __future__ import annotations

import torch
from typing import List, Dict
from neuralogix.core.ir.graph import TypedGraph
from neuralogix.core.ir.schema import NodeType
from neuralogix.core.codec.vq import VQCodec


class VQTrainer:
    """Trains VQ codebooks using data from graphs."""

    def __init__(self, codec: VQCodec):
        """Initialize trainer with a codec to be trained.
        
        Args:
            codec: VQCodec instance
        """
        self.codec = codec

    def train(self, graphs: List[TypedGraph], iterations: int = 10, seed: int = 42):
        """Train codebooks using K-Means on node embeddings.
        
        Args:
            graphs: List of graphs to use for training
            iterations: Number of K-Means iterations
            seed: For determinism (Phase A)
        """
        torch.manual_seed(seed)
        # 1. Collect embeddings by type
        embeddings_by_type: Dict[str, List[torch.Tensor]] = {
            t.value: [] for t in NodeType
        }
        
        for g in graphs:
            for node in g.nodes.values():
                node_type = node.node_type.value if hasattr(node.node_type, "value") else str(node.node_type)
                if node_type in embeddings_by_type:
                    emb = self.codec._embed(node)
                    embeddings_by_type[node_type].append(emb)
                    
        # 2. Run K-Means for each type
        for node_type, embs in embeddings_by_type.items():
            if not embs:
                continue
                
            data = torch.stack(embs) # [N, dimension]
            
            # Initialize centroids
            num_samples = data.size(0)
            num_clusters = min(self.codec.codebook_size, num_samples)
            
            indices = torch.randperm(num_samples)[:num_clusters]
            centroids = data[indices].clone()
            
            # Simple K-Means
            for it in range(iterations):
                # Compute distances
                dist = torch.cdist(data, centroids)
                
                # Assign to nearest centroid
                assignments = torch.argmin(dist, dim=1)
                
                # Update centroids
                new_centroids = torch.zeros_like(centroids)
                counts = torch.zeros(num_clusters)
                
                for i in range(num_samples):
                    cluster_idx = assignments[i]
                    new_centroids[cluster_idx] += data[i]
                    counts[cluster_idx] += 1
                
                mask = counts > 0
                new_centroids[mask] /= counts[mask].unsqueeze(1)
                
                if not mask.all():
                    empty_indices = torch.where(~mask)[0]
                    random_indices = torch.randperm(num_samples)[:len(empty_indices)]
                    new_centroids[empty_indices] = data[random_indices]
                
                centroids = new_centroids
                
            # Update codebook
            if num_clusters < self.codec.codebook_size:
                final_codebook = torch.zeros((self.codec.codebook_size, self.codec.dimension))
                final_codebook[:num_clusters] = centroids
                self.codec.codebooks[node_type] = final_codebook
            else:
                self.codec.codebooks[node_type] = centroids
                
        print(f"Training complete. Codebooks populated for types: {[t for t, v in embeddings_by_type.items() if v]}")
