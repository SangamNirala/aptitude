"""
Scraping Configuration for IndiaBix and GeeksforGeeks
Comprehensive source configurations with selectors, pagination, and extraction rules
"""

from typing import Dict, List, Any
from ..models.scraping_models import DataSourceConfig, ScrapingTarget, ContentExtractionMethod, ScrapingSourceType

# =============================================================================
# INDIABIX CONFIGURATION
# =============================================================================

INDIABIX_CONFIG = DataSourceConfig(
    name="IndiaBix",
    source_type=ScrapingSourceType.INDIABIX,
    base_url="https://www.indiabix.com",
    extraction_method=ContentExtractionMethod.SELENIUM,
    
    # CSS Selectors for IndiaBix
    selectors={
        # Question Elements
        "question_text": "div.bix-div-container div.bix-td-qtxt",
        "question_options": "div.bix-div-container table.bix-tbl-options td",
        "correct_answer": "div.bix-div-container div.bix-ans-description",
        "explanation": "div.bix-div-container div.bix-ans-description p",
        
        # Navigation Elements
        "next_button": "a.bix-btn-next",
        "page_numbers": "div.bix-pagination a",
        "current_page": "div.bix-pagination span.current",
        
        # Category Elements
        "category_links": "div.bix-menu-section a",
        "subcategory_links": "div.bix-submenu a",
        
        # Quality Indicators
        "question_number": "div.bix-question-number",
        "difficulty_indicator": "div.bix-difficulty",
        
        # Anti-Detection Elements
        "loading_indicator": "div.loader, .spinner",
        "captcha": "div.captcha, #captcha",
        "blocked_indicator": "div.blocked, .access-denied"
    },
    
    # Pagination Configuration
    pagination_config={
        "type": "numbered",  # numbered, infinite_scroll, next_button
        "base_url_pattern": "{base_url}/{category}/quiz?page={page}",
        "start_page": 1,
        "max_pages_per_category": 50,
        "page_param": "page",
        "questions_per_page": 1,
        "wait_after_page_load": 3.0,
        "scroll_to_load": False
    },
    
    # Rate Limiting & Ethics
    rate_limit_delay=3.0,  # 3 seconds between requests for IndiaBix
    max_concurrent_requests=2,  # Conservative for IndiaBix
    respect_robots_txt=True,
    user_agent_rotation=True
)

# IndiaBix Categories and Targets
INDIABIX_TARGETS = [
    # Quantitative Aptitude
    ScrapingTarget(
        source_id="indiabix",
        category="quantitative",
        subcategory="arithmetic_aptitude",
        target_url="https://www.indiabix.com/aptitude/arithmetic-aptitude",
        expected_question_count=500,
        question_selectors={
            "question_container": "div.bix-div-container",
            "question_text": "div.bix-td-qtxt",
            "options": "table.bix-tbl-options td",
            "answer": "div.bix-ans-description"
        },
        priority=1
    ),
    
    ScrapingTarget(
        source_id="indiabix", 
        category="quantitative",
        subcategory="simple_interest",
        target_url="https://www.indiabix.com/aptitude/simple-interest",
        expected_question_count=300,
        question_selectors={
            "question_container": "div.bix-div-container",
            "question_text": "div.bix-td-qtxt",
            "options": "table.bix-tbl-options td",
            "answer": "div.bix-ans-description"
        },
        priority=1
    ),
    
    ScrapingTarget(
        source_id="indiabix",
        category="quantitative", 
        subcategory="compound_interest",
        target_url="https://www.indiabix.com/aptitude/compound-interest",
        expected_question_count=250,
        question_selectors={
            "question_container": "div.bix-div-container",
            "question_text": "div.bix-td-qtxt", 
            "options": "table.bix-tbl-options td",
            "answer": "div.bix-ans-description"
        },
        priority=1
    ),
    
    ScrapingTarget(
        source_id="indiabix",
        category="quantitative",
        subcategory="percentage",
        target_url="https://www.indiabix.com/aptitude/percentage", 
        expected_question_count=400,
        question_selectors={
            "question_container": "div.bix-div-container",
            "question_text": "div.bix-td-qtxt",
            "options": "table.bix-tbl-options td", 
            "answer": "div.bix-ans-description"
        },
        priority=1
    ),
    
    # Logical Reasoning
    ScrapingTarget(
        source_id="indiabix",
        category="logical",
        subcategory="logical_reasoning",
        target_url="https://www.indiabix.com/logical-reasoning/logical-reasoning",
        expected_question_count=600,
        question_selectors={
            "question_container": "div.bix-div-container",
            "question_text": "div.bix-td-qtxt",
            "options": "table.bix-tbl-options td",
            "answer": "div.bix-ans-description"
        },
        priority=2
    ),
    
    ScrapingTarget(
        source_id="indiabix",
        category="logical",
        subcategory="verbal_classification",
        target_url="https://www.indiabix.com/logical-reasoning/verbal-classification",
        expected_question_count=300,
        question_selectors={
            "question_container": "div.bix-div-container",
            "question_text": "div.bix-td-qtxt",
            "options": "table.bix-tbl-options td",
            "answer": "div.bix-ans-description"
        },
        priority=2
    ),
    
    # Verbal Ability
    ScrapingTarget(
        source_id="indiabix",
        category="verbal",
        subcategory="spotting_errors",
        target_url="https://www.indiabix.com/verbal-ability/spotting-errors",
        expected_question_count=400,
        question_selectors={
            "question_container": "div.bix-div-container",
            "question_text": "div.bix-td-qtxt",
            "options": "table.bix-tbl-options td",
            "answer": "div.bix-ans-description"
        },
        priority=3
    ),
    
    ScrapingTarget(
        source_id="indiabix",
        category="verbal",
        subcategory="synonyms",
        target_url="https://www.indiabix.com/verbal-ability/synonyms",
        expected_question_count=350,
        question_selectors={
            "question_container": "div.bix-div-container",
            "question_text": "div.bix-td-qtxt",
            "options": "table.bix-tbl-options td",
            "answer": "div.bix-ans-description"
        },
        priority=3
    )
]

# =============================================================================
# GEEKSFORGEEKS CONFIGURATION
# =============================================================================

GEEKSFORGEEKS_CONFIG = DataSourceConfig(
    name="GeeksforGeeks",
    source_type=ScrapingSourceType.GEEKSFORGEEKS,
    base_url="https://www.geeksforgeeks.org",
    extraction_method=ContentExtractionMethod.PLAYWRIGHT,  # More dynamic content
    
    # CSS Selectors for GeeksforGeeks
    selectors={
        # Question Elements
        "question_text": "div.problemStatement p, div.problem-statement",
        "question_options": "div.options label, ul.mcq-options li",
        "correct_answer": "div.solution-approach, div.correct-answer", 
        "explanation": "div.article-content, div.solution-explanation",
        
        # Navigation Elements
        "next_button": "a.next-problem, button.next",
        "page_numbers": "div.pagination a, nav.pagination a",
        "load_more": "button.load-more, a.load-more",
        
        # Category Elements
        "category_links": "nav.category-nav a, div.categories a",
        "topic_links": "div.topics-list a",
        
        # Dynamic Content
        "lazy_loaded_content": "div[data-lazy], img[data-src]",
        "ajax_container": "div.ajax-content",
        
        # Quality Indicators
        "difficulty_badge": "span.difficulty, div.difficulty-level",
        "company_tags": "div.company-tags span, a.company-tag",
        "topic_tags": "div.topic-tags a, span.topic",
        
        # Anti-Detection Elements
        "loading_spinner": "div.spinner, .loading",
        "captcha": "div.g-recaptcha, #captcha-container",
        "rate_limit_warning": "div.rate-limit, .too-many-requests"
    },
    
    # Pagination Configuration  
    pagination_config={
        "type": "infinite_scroll",  # GeeksforGeeks uses infinite scroll
        "base_url_pattern": "{base_url}/practice/{category}",
        "scroll_pause_time": 2.0,
        "max_scrolls": 20,
        "scroll_height_threshold": 0.8,  # Scroll when 80% of page viewed
        "wait_for_content": 3.0,
        "detect_end_of_content": True,
        "end_of_content_selectors": ["div.no-more-content", "p.end-of-results"]
    },
    
    # Rate Limiting & Ethics
    rate_limit_delay=2.5,  # 2.5 seconds for GeeksforGeeks
    max_concurrent_requests=3,
    respect_robots_txt=True,
    user_agent_rotation=True
)

# GeeksforGeeks Categories and Targets
GEEKSFORGEEKS_TARGETS = [
    # Data Structures & Algorithms (Core CS topics)
    ScrapingTarget(
        source_id="geeksforgeeks",
        category="data_structures",
        subcategory="arrays",
        target_url="https://www.geeksforgeeks.org/practice/data-structures/arrays",
        expected_question_count=800,
        question_selectors={
            "question_container": "div.problem-container",
            "question_text": "div.problem-statement",
            "options": "div.options label",
            "solution": "div.solution-approach"
        },
        custom_extraction_rules={
            "wait_for_dynamic_content": True,
            "scroll_to_load_more": True,
            "handle_code_blocks": True
        },
        priority=1
    ),
    
    ScrapingTarget(
        source_id="geeksforgeeks",
        category="algorithms",
        subcategory="sorting_searching",
        target_url="https://www.geeksforgeeks.org/practice/algorithms/sorting",
        expected_question_count=600,
        question_selectors={
            "question_container": "div.problem-container",
            "question_text": "div.problem-statement", 
            "options": "div.options label",
            "solution": "div.solution-approach"
        },
        priority=1
    ),
    
    # Quantitative & Aptitude
    ScrapingTarget(
        source_id="geeksforgeeks",
        category="quantitative",
        subcategory="mathematical_aptitude", 
        target_url="https://www.geeksforgeeks.org/practice/mathematical-aptitude",
        expected_question_count=400,
        question_selectors={
            "question_container": "div.aptitude-container",
            "question_text": "div.question-text",
            "options": "ul.mcq-options li",
            "answer": "div.correct-answer"
        },
        priority=2
    ),
    
    ScrapingTarget(
        source_id="geeksforgeeks",
        category="logical",
        subcategory="programming_puzzles",
        target_url="https://www.geeksforgeeks.org/practice/puzzles",
        expected_question_count=300,
        question_selectors={
            "question_container": "div.puzzle-container",
            "question_text": "div.puzzle-statement",
            "answer": "div.puzzle-solution",
            "explanation": "div.puzzle-explanation"
        },
        priority=2
    ),
    
    # Computer Science Fundamentals
    ScrapingTarget(
        source_id="geeksforgeeks",
        category="cs_fundamentals",
        subcategory="operating_systems",
        target_url="https://www.geeksforgeeks.org/practice/operating-systems",
        expected_question_count=350,
        question_selectors={
            "question_container": "div.mcq-container",
            "question_text": "div.question",
            "options": "div.options label",
            "explanation": "div.explanation"
        },
        priority=3
    ),
    
    ScrapingTarget(
        source_id="geeksforgeeks",
        category="cs_fundamentals", 
        subcategory="database_management",
        target_url="https://www.geeksforgeeks.org/practice/database-management",
        expected_question_count=400,
        question_selectors={
            "question_container": "div.mcq-container",
            "question_text": "div.question",
            "options": "div.options label", 
            "explanation": "div.explanation"
        },
        priority=3
    )
]

# =============================================================================
# SOURCE MANAGEMENT CONFIGURATION
# =============================================================================

# Source Priority Mapping
SOURCE_PRIORITY_CONFIG = {
    "indiabix": {
        "default_priority": 1,
        "high_value_categories": ["quantitative", "logical"],
        "rate_limit_multiplier": 1.5  # More conservative
    },
    "geeksforgeeks": {
        "default_priority": 2, 
        "high_value_categories": ["data_structures", "algorithms"],
        "rate_limit_multiplier": 1.2
    }
}

# Quality Thresholds by Source
SOURCE_QUALITY_THRESHOLDS = {
    "indiabix": {
        "auto_approve": 85.0,  # Higher threshold for IndiaBix
        "auto_reject": 60.0,
        "human_review_range": (60.0, 85.0)
    },
    "geeksforgeeks": {
        "auto_approve": 80.0,
        "auto_reject": 55.0, 
        "human_review_range": (55.0, 80.0)
    }
}

# Anti-Detection Strategies by Source
ANTI_DETECTION_CONFIG = {
    "indiabix": {
        "user_agents": [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ],
        "request_headers": {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        },
        "delay_range": (2.0, 5.0),  # Random delay between 2-5 seconds
        "session_rotation_frequency": 50  # New session every 50 requests
    },
    "geeksforgeeks": {
        "user_agents": [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
            "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/119.0"
        ],
        "request_headers": {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache"
        },
        "delay_range": (1.5, 4.0),
        "session_rotation_frequency": 75
    }
}

# =============================================================================
# EXTRACTION VALIDATION RULES
# =============================================================================

EXTRACTION_VALIDATION_RULES = {
    "question_text": {
        "min_length": 10,
        "max_length": 2000,
        "required_patterns": [],
        "forbidden_patterns": ["advertisement", "click here", "subscribe"]
    },
    "options": {
        "min_count": 2,
        "max_count": 6,
        "min_option_length": 1,
        "max_option_length": 200
    },
    "correct_answer": {
        "must_match_option": True,
        "confidence_threshold": 0.8
    },
    "explanation": {
        "min_length": 20,
        "max_length": 5000,
        "optional": True
    }
}

# Content Quality Indicators
CONTENT_QUALITY_INDICATORS = {
    "positive_indicators": [
        "step-by-step solution",
        "detailed explanation", 
        "multiple choice",
        "correct answer",
        "difficulty level",
        "topic classification"
    ],
    "negative_indicators": [
        "incomplete question",
        "missing options",
        "unclear statement",
        "broken formatting",
        "advertising content",
        "duplicate content"
    ],
    "quality_weights": {
        "completeness": 0.3,
        "clarity": 0.25, 
        "accuracy": 0.25,
        "formatting": 0.2
    }
}

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_source_config(source_name: str) -> DataSourceConfig:
    """Get configuration for a specific source"""
    if source_name.lower() == "indiabix":
        return INDIABIX_CONFIG
    elif source_name.lower() == "geeksforgeeks":
        return GEEKSFORGEEKS_CONFIG
    else:
        raise ValueError(f"Unknown source: {source_name}")

def get_source_targets(source_name: str) -> List[ScrapingTarget]:
    """Get scraping targets for a specific source"""
    if source_name.lower() == "indiabix":
        return INDIABIX_TARGETS
    elif source_name.lower() == "geeksforgeeks":
        return GEEKSFORGEEKS_TARGETS
    else:
        raise ValueError(f"Unknown source: {source_name}")

def get_quality_thresholds(source_name: str) -> Dict[str, float]:
    """Get quality thresholds for a specific source"""
    return SOURCE_QUALITY_THRESHOLDS.get(source_name.lower(), {
        "auto_approve": 75.0,
        "auto_reject": 50.0, 
        "human_review_range": (50.0, 75.0)
    })

def get_anti_detection_config(source_name: str) -> Dict[str, Any]:
    """Get anti-detection configuration for a specific source"""
    return ANTI_DETECTION_CONFIG.get(source_name.lower(), {
        "user_agents": ["Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"],
        "delay_range": (2.0, 4.0),
        "session_rotation_frequency": 50
    })

# Export all configurations
__all__ = [
    'INDIABIX_CONFIG', 'GEEKSFORGEEKS_CONFIG',
    'INDIABIX_TARGETS', 'GEEKSFORGEEKS_TARGETS', 
    'SOURCE_PRIORITY_CONFIG', 'SOURCE_QUALITY_THRESHOLDS',
    'ANTI_DETECTION_CONFIG', 'EXTRACTION_VALIDATION_RULES',
    'CONTENT_QUALITY_INDICATORS',
    'get_source_config', 'get_source_targets',
    'get_quality_thresholds', 'get_anti_detection_config'
]