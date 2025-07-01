import hashlib

class PersistentKVCacheManager:
    def __init__(self):
        self.base_context_cached = False
        self.base_context_tokens = 0
        self.cache_hits = 0
        self.cache_misses = 0
        self.base_context_hash = None
        self.evaluation_count = 0
        self.evaluation_context_active = False

    def should_build_base_cache(self, base_context: str) -> bool:
        current_hash = hashlib.md5(base_context.encode()).hexdigest()
        
        if not self.base_context_cached or self.base_context_hash != current_hash:
            self.base_context_hash = current_hash
            self.cache_misses += 1
            return True
        
        self.cache_hits += 1
        return False
    
    def mark_base_cache_built(self, token_count: int):
        self.base_context_cached = True
        self.base_context_tokens = token_count
        print(f"✓ Base context cached ({token_count} tokens)")
    
    def increment_evaluation_count(self):
        self.evaluation_count += 1
        self.evaluation_context_active = True
    
    def should_clear_evaluation_context(self) -> bool:
        """Determine if evaluation context should be cleared"""
        # Clear after every evaluation
        return self.evaluation_context_active
    
    def clear_evaluation_context(self):
        """Clear ONLY evaluation-specific state"""
        self.evaluation_context_active = False
        print("🔄 Cleared evaluation context")
    
    def reset_base_cache(self):
        """Full reset (only for base context changes)"""
        self.base_context_cached = False
        self.base_context_tokens = 0
        print("♻️ Full cache reset")
    
    def get_stats(self) -> dict:
        total = self.cache_hits + self.cache_misses
        hit_rate = (self.cache_hits / total * 100) if total > 0 else 0
        return {
            "hits": self.cache_hits,
            "misses": self.cache_misses,
            "hit_rate": f"{hit_rate:.1f}%",
            "base_cached": self.base_context_cached,
            "base_tokens": self.base_context_tokens,
            "evaluations_performed": self.evaluation_count
        }

    
    # ... (rest of PersistentKVCacheManager implementation from original code)