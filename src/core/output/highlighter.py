"""
Text highlighting utility for keyword highlighting in summaries.
"""
import re
from typing import List, Tuple, Dict, Any


class TextHighlighter:
    """Highlights keywords in text using HTML spans."""
    
    # Define keyword categories and corresponding style classes
    KEYWORD_PATTERNS = [
        # Risk-related keywords
        {
            "pattern": re.compile(r'\b(danger|risk|warning|caution|careful|safe|dangerous|risky)\b|\b(high|medium|low)\s+risk\b', re.IGNORECASE),
            "className": 'risk-keyword'
        },
        # Action-related keywords
        {
            "pattern": re.compile(r'\b(authorize|authorization|approval|transfer|transaction|signature|confirm|login|vote|mint|burn|stake|unstake)\b', re.IGNORECASE),
            "className": 'action-keyword'
        },
        # Amount and token related
        {
            # Match: numbers with commas (1,000), numbers with decimals (100.5)
            # Match patterns in order of priority (longer matches first):
            # 1. Number + token (e.g., "1,000 USD Coin", "1,000 USD")
            # 2. Standalone numbers (e.g., "1,000")
            # 3. Standalone tokens (e.g., "USD", "Coin")
            "pattern": re.compile(
                r'\b(\d{1,3}(?:,\d{3})*(?:\.\d+)?|\d+\.?\d*)\s+(USD|USDT|USDC|ETH)\s+Coin\b|'  # "1,000 USD Coin"
                r'\b(\d{1,3}(?:,\d{3})*(?:\.\d+)?|\d+\.?\d*)\s+(USD|USDT|USDC|ETH|Coin|token)\b|'  # "1,000 USD" or "1,000 Coin"
                r'\b(\d{1,3}(?:,\d{3})*(?:\.\d+)?|\d+\.?\d*)\b|'  # Standalone numbers like "1,000"
                r'\b(USD|USDT|USDC|ETH|Coin|token)\b',  # Standalone tokens
                re.IGNORECASE
            ),
            "className": 'amount-keyword'
        },
        # Contract and address related
        {
            "pattern": re.compile(r'\b(smart\s+contract|contract|address)\b|(0x[a-fA-F0-9]{40})', re.IGNORECASE),
            "className": 'keyword-highlight'
        },
        # General important keywords
        {
            "pattern": re.compile(r'\b(unlimited|permanent|all|entire|infinite|permit|approve)\b', re.IGNORECASE),
            "className": 'keyword-highlight'
        }
    ]
    
    @staticmethod
    def highlight_keywords(text: str) -> str:
        """
        Highlight keywords in text using HTML spans.
        
        Args:
            text: Plain text to highlight
            
        Returns:
            HTML string with highlighted keywords
        """
        if not text:
            return text
        
        # Collect all matches with their positions
        matches: List[Dict[str, Any]] = []
        
        for pattern_info in TextHighlighter.KEYWORD_PATTERNS:
            pattern = pattern_info["pattern"]
            className = pattern_info["className"]
            
            for match in pattern.finditer(text):
                matches.append({
                    "start": match.start(),
                    "end": match.end(),
                    "text": match.group(0),
                    "className": className
                })
        
        # Sort matches by length (longer first), then by start position
        # This ensures longer matches are processed first and kept when overlapping
        matches.sort(key=lambda m: (-(m["end"] - m["start"]), m["start"]))
        
        # Remove overlapping matches (keep longer ones that were processed first)
        filtered_matches: List[Dict[str, Any]] = []
        for current in matches:
            overlap = False
            
            # Check if current match overlaps with any already filtered match
            for existing in filtered_matches:
                if current["start"] < existing["end"] and current["end"] > existing["start"]:
                    overlap = True
                    break
            
            if not overlap:
                filtered_matches.append(current)
        
        # Sort by start position descending for replacement (from end to start)
        filtered_matches.sort(key=lambda m: -m["start"])
        
        # Replace matches from end to start to avoid position shifting
        highlighted_text = text
        for match_info in filtered_matches:
            start = match_info["start"]
            end = match_info["end"]
            match_text = match_info["text"]
            className = match_info["className"]
            
            before = highlighted_text[:start]
            after = highlighted_text[end:]
            highlighted_text = before + f'<span class="{className}">{match_text}</span>' + after
        
        return highlighted_text

