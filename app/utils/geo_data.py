"""
Utility functions for fetching geographic data (countries and US states) from public APIs.
Uses REST Countries API for countries and falls back to hardcoded data if API fails.
"""
import httpx
import json
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

# Cache for countries list to avoid repeated API calls
_countries_cache: Optional[List[str]] = None

# Fallback hardcoded countries list (includes regional countries relevant to Aruba)
FALLBACK_COUNTRIES = [
    "Afghanistan", "Albania", "Algeria", "Andorra", "Angola", "Antigua and Barbuda",
    "Argentina", "Armenia", "Aruba", "Australia", "Austria", "Azerbaijan",
    "Bahamas", "Bahrain", "Bangladesh", "Barbados", "Belarus", "Belgium",
    "Belize", "Benin", "Bhutan", "Bolivia", "Bosnia and Herzegovina", "Botswana",
    "Brazil", "Brunei", "Bulgaria", "Burkina Faso", "Burundi", "Cabo Verde",
    "Cambodia", "Cameroon", "Canada", "Central African Republic", "Chad", "Chile",
    "China", "Colombia", "Comoros", "Congo (Congo-Brazzaville)", "Costa Rica",
    "Côte d'Ivoire", "Croatia", "Cuba", "Cyprus", "Czech Republic",
    "Democratic Republic of the Congo", "Denmark", "Djibouti", "Dominica",
    "Dominican Republic", "Ecuador", "Egypt", "El Salvador", "Equatorial Guinea",
    "Eritrea", "Estonia", "Eswatini", "Ethiopia", "Fiji", "Finland", "France",
    "Gabon", "Gambia", "Georgia", "Germany", "Ghana", "Greece", "Grenada",
    "Guatemala", "Guinea", "Guinea-Bissau", "Guyana", "Haiti", "Honduras",
    "Hungary", "Iceland", "India", "Indonesia", "Iran", "Iraq", "Ireland",
    "Israel", "Italy", "Jamaica", "Japan", "Jordan", "Kazakhstan", "Kenya",
    "Kiribati", "Kuwait", "Kyrgyzstan", "Laos", "Latvia", "Lebanon", "Lesotho",
    "Liberia", "Libya", "Liechtenstein", "Lithuania", "Luxembourg", "Madagascar",
    "Malawi", "Malaysia", "Maldives", "Mali", "Malta", "Marshall Islands",
    "Mauritania", "Mauritius", "Mexico", "Micronesia", "Moldova", "Monaco",
    "Mongolia", "Montenegro", "Morocco", "Mozambique", "Myanmar", "Namibia",
    "Nauru", "Nepal", "Netherlands", "New Zealand", "Nicaragua", "Niger",
    "Nigeria", "North Macedonia", "Norway", "Oman", "Pakistan", "Palau",
    "Panama", "Papua New Guinea", "Paraguay", "Peru", "Philippines", "Poland",
    "Portugal", "Qatar", "Romania", "Russia", "Rwanda", "Saint Kitts and Nevis",
    "Saint Lucia", "Saint Vincent and the Grenadines", "Samoa", "San Marino",
    "Sao Tome and Principe", "Saudi Arabia", "Senegal", "Serbia", "Seychelles",
    "Sierra Leone", "Singapore", "Slovakia", "Slovenia", "Solomon Islands",
    "Somalia", "South Africa", "South Korea", "South Sudan", "Spain", "Sri Lanka",
    "Sudan", "Suriname", "Sweden", "Switzerland", "Syria", "Taiwan", "Tajikistan",
    "Tanzania", "Thailand", "Timor-Leste", "Togo", "Tonga", "Trinidad and Tobago",
    "Tunisia", "Turkey", "Turkmenistan", "Tuvalu", "Uganda", "Ukraine",
    "United Arab Emirates", "United Kingdom", "United States", "Uruguay",
    "Uzbekistan", "Vanuatu", "Vatican City", "Venezuela", "Vietnam", "Yemen",
    "Zambia", "Zimbabwe", "Bonaire", "Curacao", "Saint Martin",
]

# US States list (static since they don't change)
US_STATES = [
    "Alabama", "Alaska", "Arizona", "Arkansas", "California", "Colorado",
    "Connecticut", "Delaware", "Florida", "Georgia", "Hawaii", "Idaho",
    "Illinois", "Indiana", "Iowa", "Kansas", "Kentucky", "Louisiana",
    "Maine", "Maryland", "Massachusetts", "Michigan", "Minnesota",
    "Mississippi", "Missouri", "Montana", "Nebraska", "Nevada",
    "New Hampshire", "New Jersey", "New Mexico", "New York",
    "North Carolina", "North Dakota", "Ohio", "Oklahoma", "Oregon",
    "Pennsylvania", "Rhode Island", "South Carolina", "South Dakota",
    "Tennessee", "Texas", "Utah", "Vermont", "Virginia", "Washington",
    "West Virginia", "Wisconsin", "Wyoming",
]


async def fetch_countries_from_api() -> Optional[List[str]]:
    """
    Fetch countries list from REST Countries API.
    
    Returns:
        List of country names sorted alphabetically, or None if API call fails.
    """
    try:
        url = "https://restcountries.com/v3.1/all?fields=name"
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()
            
            # Extract country names from API response
            countries = []
            for country in data:
                # Use common name, fallback to official name
                name = country.get("name", {})
                country_name = name.get("common") or name.get("official")
                if country_name:
                    countries.append(country_name)
            
            # Add regional countries that might not be in the API
            regional_countries = ["Bonaire", "Curacao", "Saint Martin"]
            for regional in regional_countries:
                if regional not in countries:
                    countries.append(regional)
            
            # Sort alphabetically
            return sorted(set(countries))
            
    except Exception as e:
        logger.warning(f"Failed to fetch countries from API: {e}. Using fallback data.")
        return None


def get_country_list() -> List[str]:
    """
    Return a list of countries, fetched from API if available, otherwise using fallback.
    This is a synchronous wrapper that attempts to fetch from API on first call.
    
    Returns:
        Alphabetically sorted list of country names.
    """
    global _countries_cache
    
    # Return cached data if available
    if _countries_cache is not None:
        return _countries_cache
    
    # Try to fetch from API synchronously (only on first call)
    # If we're in an async context, we'll use fallback and let async version handle it
    try:
        import asyncio
        
        # Check if we're in an async context
        try:
            loop = asyncio.get_running_loop()
            # If loop is running, use fallback (async version should be called instead)
            logger.info("Running in async context, using fallback countries. Use get_country_list_async() for API fetch.")
            _countries_cache = sorted(set(FALLBACK_COUNTRIES))
            return _countries_cache
        except RuntimeError:
            # No running loop, safe to create one
            pass
        
        # Try to fetch from API
        countries = asyncio.run(fetch_countries_from_api())
        if countries and len(countries) > 0:
            _countries_cache = countries
            logger.info(f"Successfully fetched {len(countries)} countries from API")
            return _countries_cache
    except Exception as e:
        logger.warning(f"Could not fetch countries from API: {e}. Using fallback.")
    
    # Fallback to hardcoded list
    _countries_cache = sorted(set(FALLBACK_COUNTRIES))
    logger.info(f"Using fallback countries list ({len(_countries_cache)} countries)")
    return _countries_cache


async def get_country_list_async() -> List[str]:
    """
    Async version of get_country_list() that fetches from API.
    
    Returns:
        Alphabetically sorted list of country names.
    """
    global _countries_cache
    
    # Return cached data if available
    if _countries_cache is not None:
        return _countries_cache
    
    # Fetch from API
    countries = await fetch_countries_from_api()
    if countries:
        _countries_cache = countries
        return _countries_cache
    
    # Fallback to hardcoded list
    _countries_cache = sorted(set(FALLBACK_COUNTRIES))
    return _countries_cache


def get_us_states() -> List[str]:
    """
    Return list of US states.
    
    Returns:
        List of US state names.
    """
    return US_STATES.copy()
