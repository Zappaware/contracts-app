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


# Cache for country calling codes
_calling_codes_cache: Optional[List[dict]] = None


async def fetch_calling_codes_from_api() -> Optional[List[dict]]:
    """
    Fetch country calling codes from REST Countries API.
    Uses both idd field (v3.1 format) and callingCodes field (v2 format) for compatibility.
    
    Returns:
        List of dicts with 'code' and 'country' keys, or None if API call fails.
        Format: [{"code": "+1", "country": "United States"}, ...]
    """
    try:
        # Fetch all countries with name and calling code information
        url = "https://restcountries.com/v3.1/all?fields=name,idd,callingCodes"
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()
            
            calling_codes = []
            seen_codes = set()  # Track codes to avoid duplicates
            
            for country in data:
                name = country.get("name", {})
                country_name = name.get("common") or name.get("official")
                
                if not country_name:
                    continue
                
                # Try v3.1 format first (idd field)
                idd = country.get("idd", {})
                root = idd.get("root", "")
                suffixes = idd.get("suffixes", [])
                
                if root and suffixes:
                    # Create entries for all suffixes
                    for suffix in suffixes:
                        code = f"{root}{suffix}"
                        if code not in seen_codes:
                            seen_codes.add(code)
                            calling_codes.append({
                                "code": code,
                                "country": country_name
                            })
                else:
                    # Fallback to v2 format (callingCodes array)
                    calling_codes_v2 = country.get("callingCodes", [])
                    if calling_codes_v2:
                        for code_str in calling_codes_v2:
                            # Ensure code starts with +
                            code = code_str if code_str.startswith('+') else f"+{code_str}"
                            if code not in seen_codes:
                                seen_codes.add(code)
                                calling_codes.append({
                                    "code": code,
                                    "country": country_name
                                })
            
            # Sort by country name
            calling_codes.sort(key=lambda x: x["country"])
            logger.info(f"Fetched {len(calling_codes)} calling codes for {len(set(c['country'] for c in calling_codes))} countries")
            return calling_codes
            
    except Exception as e:
        logger.warning(f"Failed to fetch calling codes from API: {e}. Using fallback data.")
        return None


def get_calling_codes_list() -> List[dict]:
    """
    Return a list of country calling codes, fetched from API if available, otherwise using fallback.
    
    Returns:
        List of dicts with 'code' and 'country' keys.
        Format: [{"code": "+1", "country": "United States"}, ...]
    """
    global _calling_codes_cache
    
    # Return cached data if available
    if _calling_codes_cache is not None:
        return _calling_codes_cache
    
    # Try to fetch from API synchronously
    try:
        import asyncio
        
        # Check if we're in an async context
        try:
            loop = asyncio.get_running_loop()
            # If loop is running, use fallback
            logger.info("Running in async context, using fallback calling codes.")
            _calling_codes_cache = _get_fallback_calling_codes()
            return _calling_codes_cache
        except RuntimeError:
            # No running loop, safe to create one
            pass
        
        # Try to fetch from API
        codes = asyncio.run(fetch_calling_codes_from_api())
        if codes and len(codes) > 0:
            _calling_codes_cache = codes
            logger.info(f"Successfully fetched {len(codes)} calling codes from API")
            return _calling_codes_cache
    except Exception as e:
        logger.warning(f"Could not fetch calling codes from API: {e}. Using fallback.")
    
    # Fallback to hardcoded list
    _calling_codes_cache = _get_fallback_calling_codes()
    logger.info(f"Using fallback calling codes list ({len(_calling_codes_cache)} codes)")
    return _calling_codes_cache


def _get_fallback_calling_codes() -> List[dict]:
    """
    Return fallback calling codes list (comprehensive list matching FALLBACK_COUNTRIES).
    This ensures every country in the countries list has a corresponding calling code.
    
    Returns:
        List of dicts with 'code' and 'country' keys.
    """
    # Comprehensive calling codes matching all countries in FALLBACK_COUNTRIES
    return [
        {"code": "+93", "country": "Afghanistan"},
        {"code": "+355", "country": "Albania"},
        {"code": "+213", "country": "Algeria"},
        {"code": "+376", "country": "Andorra"},
        {"code": "+244", "country": "Angola"},
        {"code": "+1", "country": "Antigua and Barbuda"},
        {"code": "+54", "country": "Argentina"},
        {"code": "+374", "country": "Armenia"},
        {"code": "+297", "country": "Aruba"},
        {"code": "+61", "country": "Australia"},
        {"code": "+43", "country": "Austria"},
        {"code": "+994", "country": "Azerbaijan"},
        {"code": "+1", "country": "Bahamas"},
        {"code": "+973", "country": "Bahrain"},
        {"code": "+880", "country": "Bangladesh"},
        {"code": "+1", "country": "Barbados"},
        {"code": "+375", "country": "Belarus"},
        {"code": "+32", "country": "Belgium"},
        {"code": "+501", "country": "Belize"},
        {"code": "+229", "country": "Benin"},
        {"code": "+975", "country": "Bhutan"},
        {"code": "+591", "country": "Bolivia"},
        {"code": "+387", "country": "Bosnia and Herzegovina"},
        {"code": "+267", "country": "Botswana"},
        {"code": "+55", "country": "Brazil"},
        {"code": "+673", "country": "Brunei"},
        {"code": "+359", "country": "Bulgaria"},
        {"code": "+226", "country": "Burkina Faso"},
        {"code": "+257", "country": "Burundi"},
        {"code": "+238", "country": "Cabo Verde"},
        {"code": "+855", "country": "Cambodia"},
        {"code": "+237", "country": "Cameroon"},
        {"code": "+1", "country": "Canada"},
        {"code": "+236", "country": "Central African Republic"},
        {"code": "+235", "country": "Chad"},
        {"code": "+56", "country": "Chile"},
        {"code": "+86", "country": "China"},
        {"code": "+57", "country": "Colombia"},
        {"code": "+269", "country": "Comoros"},
        {"code": "+242", "country": "Congo (Congo-Brazzaville)"},
        {"code": "+506", "country": "Costa Rica"},
        {"code": "+225", "country": "Côte d'Ivoire"},
        {"code": "+385", "country": "Croatia"},
        {"code": "+53", "country": "Cuba"},
        {"code": "+357", "country": "Cyprus"},
        {"code": "+420", "country": "Czech Republic"},
        {"code": "+243", "country": "Democratic Republic of the Congo"},
        {"code": "+45", "country": "Denmark"},
        {"code": "+253", "country": "Djibouti"},
        {"code": "+1", "country": "Dominica"},
        {"code": "+1", "country": "Dominican Republic"},
        {"code": "+593", "country": "Ecuador"},
        {"code": "+20", "country": "Egypt"},
        {"code": "+503", "country": "El Salvador"},
        {"code": "+240", "country": "Equatorial Guinea"},
        {"code": "+291", "country": "Eritrea"},
        {"code": "+372", "country": "Estonia"},
        {"code": "+268", "country": "Eswatini"},
        {"code": "+251", "country": "Ethiopia"},
        {"code": "+679", "country": "Fiji"},
        {"code": "+358", "country": "Finland"},
        {"code": "+33", "country": "France"},
        {"code": "+241", "country": "Gabon"},
        {"code": "+220", "country": "Gambia"},
        {"code": "+995", "country": "Georgia"},
        {"code": "+49", "country": "Germany"},
        {"code": "+233", "country": "Ghana"},
        {"code": "+30", "country": "Greece"},
        {"code": "+1", "country": "Grenada"},
        {"code": "+502", "country": "Guatemala"},
        {"code": "+224", "country": "Guinea"},
        {"code": "+245", "country": "Guinea-Bissau"},
        {"code": "+592", "country": "Guyana"},
        {"code": "+509", "country": "Haiti"},
        {"code": "+504", "country": "Honduras"},
        {"code": "+36", "country": "Hungary"},
        {"code": "+354", "country": "Iceland"},
        {"code": "+91", "country": "India"},
        {"code": "+62", "country": "Indonesia"},
        {"code": "+98", "country": "Iran"},
        {"code": "+964", "country": "Iraq"},
        {"code": "+353", "country": "Ireland"},
        {"code": "+972", "country": "Israel"},
        {"code": "+39", "country": "Italy"},
        {"code": "+1", "country": "Jamaica"},
        {"code": "+81", "country": "Japan"},
        {"code": "+962", "country": "Jordan"},
        {"code": "+7", "country": "Kazakhstan"},
        {"code": "+254", "country": "Kenya"},
        {"code": "+686", "country": "Kiribati"},
        {"code": "+965", "country": "Kuwait"},
        {"code": "+996", "country": "Kyrgyzstan"},
        {"code": "+856", "country": "Laos"},
        {"code": "+371", "country": "Latvia"},
        {"code": "+961", "country": "Lebanon"},
        {"code": "+266", "country": "Lesotho"},
        {"code": "+231", "country": "Liberia"},
        {"code": "+218", "country": "Libya"},
        {"code": "+423", "country": "Liechtenstein"},
        {"code": "+370", "country": "Lithuania"},
        {"code": "+352", "country": "Luxembourg"},
        {"code": "+261", "country": "Madagascar"},
        {"code": "+265", "country": "Malawi"},
        {"code": "+60", "country": "Malaysia"},
        {"code": "+960", "country": "Maldives"},
        {"code": "+223", "country": "Mali"},
        {"code": "+356", "country": "Malta"},
        {"code": "+692", "country": "Marshall Islands"},
        {"code": "+222", "country": "Mauritania"},
        {"code": "+230", "country": "Mauritius"},
        {"code": "+52", "country": "Mexico"},
        {"code": "+691", "country": "Micronesia"},
        {"code": "+373", "country": "Moldova"},
        {"code": "+377", "country": "Monaco"},
        {"code": "+976", "country": "Mongolia"},
        {"code": "+382", "country": "Montenegro"},
        {"code": "+212", "country": "Morocco"},
        {"code": "+258", "country": "Mozambique"},
        {"code": "+95", "country": "Myanmar"},
        {"code": "+264", "country": "Namibia"},
        {"code": "+674", "country": "Nauru"},
        {"code": "+977", "country": "Nepal"},
        {"code": "+31", "country": "Netherlands"},
        {"code": "+64", "country": "New Zealand"},
        {"code": "+505", "country": "Nicaragua"},
        {"code": "+227", "country": "Niger"},
        {"code": "+234", "country": "Nigeria"},
        {"code": "+389", "country": "North Macedonia"},
        {"code": "+47", "country": "Norway"},
        {"code": "+968", "country": "Oman"},
        {"code": "+92", "country": "Pakistan"},
        {"code": "+680", "country": "Palau"},
        {"code": "+507", "country": "Panama"},
        {"code": "+675", "country": "Papua New Guinea"},
        {"code": "+595", "country": "Paraguay"},
        {"code": "+51", "country": "Peru"},
        {"code": "+63", "country": "Philippines"},
        {"code": "+48", "country": "Poland"},
        {"code": "+351", "country": "Portugal"},
        {"code": "+974", "country": "Qatar"},
        {"code": "+40", "country": "Romania"},
        {"code": "+7", "country": "Russia"},
        {"code": "+250", "country": "Rwanda"},
        {"code": "+1", "country": "Saint Kitts and Nevis"},
        {"code": "+1", "country": "Saint Lucia"},
        {"code": "+1", "country": "Saint Vincent and the Grenadines"},
        {"code": "+685", "country": "Samoa"},
        {"code": "+378", "country": "San Marino"},
        {"code": "+239", "country": "Sao Tome and Principe"},
        {"code": "+966", "country": "Saudi Arabia"},
        {"code": "+221", "country": "Senegal"},
        {"code": "+381", "country": "Serbia"},
        {"code": "+248", "country": "Seychelles"},
        {"code": "+232", "country": "Sierra Leone"},
        {"code": "+65", "country": "Singapore"},
        {"code": "+421", "country": "Slovakia"},
        {"code": "+386", "country": "Slovenia"},
        {"code": "+677", "country": "Solomon Islands"},
        {"code": "+252", "country": "Somalia"},
        {"code": "+27", "country": "South Africa"},
        {"code": "+82", "country": "South Korea"},
        {"code": "+211", "country": "South Sudan"},
        {"code": "+34", "country": "Spain"},
        {"code": "+94", "country": "Sri Lanka"},
        {"code": "+249", "country": "Sudan"},
        {"code": "+597", "country": "Suriname"},
        {"code": "+46", "country": "Sweden"},
        {"code": "+41", "country": "Switzerland"},
        {"code": "+963", "country": "Syria"},
        {"code": "+886", "country": "Taiwan"},
        {"code": "+992", "country": "Tajikistan"},
        {"code": "+255", "country": "Tanzania"},
        {"code": "+66", "country": "Thailand"},
        {"code": "+670", "country": "Timor-Leste"},
        {"code": "+228", "country": "Togo"},
        {"code": "+676", "country": "Tonga"},
        {"code": "+1", "country": "Trinidad and Tobago"},
        {"code": "+216", "country": "Tunisia"},
        {"code": "+90", "country": "Turkey"},
        {"code": "+993", "country": "Turkmenistan"},
        {"code": "+688", "country": "Tuvalu"},
        {"code": "+256", "country": "Uganda"},
        {"code": "+380", "country": "Ukraine"},
        {"code": "+971", "country": "United Arab Emirates"},
        {"code": "+44", "country": "United Kingdom"},
        {"code": "+1", "country": "United States"},
        {"code": "+598", "country": "Uruguay"},
        {"code": "+998", "country": "Uzbekistan"},
        {"code": "+678", "country": "Vanuatu"},
        {"code": "+39", "country": "Vatican City"},
        {"code": "+58", "country": "Venezuela"},
        {"code": "+84", "country": "Vietnam"},
        {"code": "+967", "country": "Yemen"},
        {"code": "+260", "country": "Zambia"},
        {"code": "+263", "country": "Zimbabwe"},
        {"code": "+599", "country": "Bonaire"},
        {"code": "+599", "country": "Curacao"},
        {"code": "+590", "country": "Saint Martin"},
    ]
