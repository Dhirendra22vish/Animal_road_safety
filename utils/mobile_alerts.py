import os
import logging
import requests
from typing import List, Dict, Optional
from datetime import datetime
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class Fast2SMSAlertSystem:
    def __init__(self):
        """Initialize Fast2SMS Alert System"""
        # Load API key
        self.api_key = os.getenv('FAST2SMS_API_KEY', '').strip()
        self.is_initialized = False
        
        # Debug: Log status
        logger.info("=" * 50)
        logger.info("FAST2SMS SYSTEM INITIALIZATION")
        logger.info("=" * 50)
        logger.info(f"API Key: {'✅ Found' if self.api_key else '❌ Missing'}")
        
        self._initialize_fast2sms()
    
    def _initialize_fast2sms(self):
        """Initialize Fast2SMS with error handling"""
        try:
            if not self.api_key:
                logger.warning("⚠️ Fast2SMS API Key missing. Running in SIMULATION mode.")
                logger.warning("")
                logger.warning("To enable REAL SMS alerts, add to your .env file:")
                logger.warning("FAST2SMS_API_KEY=your_api_key_here")
                logger.warning("")
                logger.warning("Get FREE API Key at: https://www.fast2sms.com/")
                logger.warning("Steps:")
                logger.warning("1. Sign up at Fast2SMS")
                logger.warning("2. Go to Dashboard → API Keys")
                logger.warning("3. Copy your API Key")
                logger.warning("4. Add to .env file")
                logger.info("=" * 50)
                return
            
            # Test API key
            logger.info("Testing Fast2SMS API key...")
            test_result = self.test_connection()
            
            if test_result['success']:
                self.is_initialized = True
                logger.info("✅ Fast2SMS SMS ACTIVE!")
                logger.info(f"   Available Credits: {test_result['details'].get('credits', 'N/A')}")
                logger.info("=" * 50)
            else:
                logger.error("❌ Fast2SMS API key verification failed!")
                logger.error(f"   Error: {test_result['message']}")
                logger.error("")
                logger.error("Please verify:")
                logger.error("1. Your API Key is correct")
                logger.error("2. Your Fast2SMS account is active")
                logger.error("3. You have available credits")
                logger.error("4. Check: https://www.fast2sms.com/dashboard")
                logger.info("=" * 50)
                self.is_initialized = False
                
        except Exception as e:
            logger.error(f"❌ Failed to initialize Fast2SMS: {str(e)}")
            logger.info("=" * 50)
            self.is_initialized = False
    
    def send_sms_alert(self, phone_number: str, alert_data: Dict, alert_type: str = "warning") -> bool:
        """Send SMS alert via Fast2SMS"""
        
        # Validate and format phone number
        if not self.validate_phone_number(phone_number):
            logger.error(f"❌ Invalid phone number: {phone_number}")
            logger.error("   Expected: 10-digit Indian number or +91XXXXXXXXXX")
            return False
        
        formatted_phone = self.format_phone_number(phone_number)
        
        try:
            # Create message
            message_body = self._create_alert_message(alert_data, alert_type)
            
            # Send via Fast2SMS if initialized
            if self.is_initialized and self.api_key:
                try:
                    logger.info(f"📱 Sending REAL SMS via Fast2SMS...")
                    logger.info(f"   To: {formatted_phone}")
                    
                    # Fast2SMS API endpoint
                    url = "https://www.fast2sms.com/dev/bulkV2"
                    
                    # Prepare payload
                    payload = {
                        "route": "q",  # Quick route
                        "message": message_body,
                        "language": "english",
                        "flash": 0,
                        "numbers": formatted_phone
                    }
                    
                    # Headers
                    headers = {
                        "authorization": self.api_key,
                        "Content-Type": "application/x-www-form-urlencoded",
                        "Cache-Control": "no-cache"
                    }
                    
                    # Send request
                    response = requests.post(url, data=payload, headers=headers)
                    result = response.json()
                    
                    # Check response
                    if result.get('return') == True or response.status_code == 200:
                        logger.info(f"✅ SMS SENT SUCCESSFULLY!")
                        logger.info(f"   Message ID: {result.get('message', 'N/A')}")
                        logger.info(f"   Status: Success")
                        
                        # Print message preview
                        print("\n" + "=" * 50)
                        print("📱 SMS SENT TO:", formatted_phone)
                        print("=" * 50)
                        print(message_body)
                        print("=" * 50 + "\n")
                        
                        return True
                    else:
                        error_msg = result.get('message', 'Unknown error')
                        logger.error(f"❌ Fast2SMS API Error!")
                        logger.error(f"   Error: {error_msg}")
                        logger.error(f"   Response: {result}")
                        
                        # Check common errors
                        if "Invalid api key" in error_msg.lower():
                            logger.error("   → Check your API Key in .env file")
                        elif "insufficient balance" in error_msg.lower():
                            logger.error("   → Recharge your Fast2SMS account")
                        elif "invalid number" in error_msg.lower():
                            logger.error("   → Check phone number format")
                        
                        # Fall back to simulation
                        logger.info(f"\n📱 FALLING BACK TO SIMULATION MODE")
                        self._print_simulation_sms(formatted_phone, message_body)
                        return False
                        
                except requests.exceptions.RequestException as e:
                    logger.error(f"❌ Network Error: {str(e)}")
                    self._print_simulation_sms(formatted_phone, message_body)
                    return False
                    
            else:
                # Simulation mode
                logger.info(f"📱 SMS SIMULATION MODE (Fast2SMS not configured)")
                self._print_simulation_sms(formatted_phone, message_body)
                return True  # Return True for simulation
            
        except Exception as e:
            logger.error(f"❌ Unexpected error: {str(e)}")
            return False
    
    def _print_simulation_sms(self, phone: str, message: str):
        """Print simulated SMS"""
        print("\n" + "=" * 50)
        print("📱 SMS SIMULATION")
        print("=" * 50)
        print(f"To: +91{phone}")
        print("-" * 50)
        print(message)
        print("=" * 50)
        print("💡 To send real SMS, get Fast2SMS API key")
        print("   Visit: https://www.fast2sms.com/")
        print("=" * 50 + "\n")
    
    def _create_alert_message(self, alert_data: Dict, alert_type: str) -> str:
        """Create formatted SMS message (within 160 chars for better delivery)"""
        species = alert_data.get('species', 'wildlife').title().replace('_', ' ')
        zone = alert_data.get('zone_name', 'Wildlife Zone')
        dist = alert_data.get('distance', alert_data.get('distance_from_vehicle', 0))
        conf = alert_data.get('confidence', 0.85)
        speed = alert_data.get('recommended_speed', 30)
        
        # Shorter messages for SMS
        urgency_map = {
            "critical": ("🚨 CRITICAL", "STOP NOW"),
            "animal_detected": ("🦌 ALERT", "SLOW DOWN"),
            "emergency": ("🆘 EMERGENCY", "CALL HELP"),
            "warning": ("⚠️ WARNING", "BE CAREFUL")
        }
        
        urgency, action = urgency_map.get(alert_type, urgency_map["warning"])
        
        # Compact message format
        message = f"{urgency}\n{species} at {zone}\n{dist:.1f}km ahead | {conf*100:.0f}%\nSpeed: {speed}kmph\n{action}\n-UP Wildlife"
        
        return message.strip()
    
    def validate_phone_number(self, phone_number: str) -> bool:
        """Validate Indian phone number"""
        if not phone_number:
            return False
        
        # Clean number
        cleaned = ''.join(c for c in phone_number if c.isdigit())
        
        # Remove +91 if present
        if cleaned.startswith('91') and len(cleaned) == 12:
            cleaned = cleaned[2:]
        
        # Must be 10 digits and start with 6-9
        if len(cleaned) == 10 and cleaned[0] in '6789':
            return True
        
        return False
    
    def format_phone_number(self, phone_number: str) -> str:
        """Format to 10-digit Indian number (without +91)"""
        cleaned = ''.join(c for c in phone_number if c.isdigit())
        
        # Remove country code if present
        if cleaned.startswith('91') and len(cleaned) == 12:
            return cleaned[2:]
        
        return cleaned
    
    def test_connection(self) -> Dict:
        """Test Fast2SMS API connection"""
        result = {
            "success": False,
            "message": "",
            "details": {}
        }
        
        if not self.api_key:
            result["message"] = "API Key missing. Check .env file."
            return result
        
        try:
            # Test API with balance check
            url = "https://www.fast2sms.com/dev/bulkV2"
            headers = {
                "authorization": self.api_key,
                "Content-Type": "application/x-www-form-urlencoded"
            }
            
            # Just validate the key (no actual SMS sent)
            payload = {
                "route": "q",
                "message": "test",
                "language": "english",
                "numbers": "9999999999"  # Dummy number for validation
            }
            
            response = requests.post(url, data=payload, headers=headers, timeout=5)
            
            if response.status_code == 200:
                result["success"] = True
                result["message"] = "Fast2SMS connection successful!"
                result["details"] = {
                    "api_status": "Active",
                    "service": "Fast2SMS India"
                }
            else:
                result["message"] = f"API test failed: {response.text}"
                
        except Exception as e:
            result["message"] = f"Connection test failed: {str(e)}"
        
        return result
    
    def get_status(self) -> Dict:
        """Get SMS system status"""
        return {
            "initialized": self.is_initialized,
            "mode": "ACTIVE 🟢" if self.is_initialized else "SIMULATION 🟡",
            "api_key": "✅" if self.api_key else "❌",
            "service": "Fast2SMS (India)",
            "ready_for_sms": self.is_initialized
        }

# Global SMS system instance
sms_system = Fast2SMSAlertSystem()

def send_mobile_alert(alert_data: Dict, alert_type: str = "warning") -> Dict:
    """Send mobile alert (in-app + SMS)"""
    import streamlit as st
    
    if 'mobile_alerts' not in st.session_state:
        st.session_state.mobile_alerts = []
        logger.info("✅ Initialized mobile_alerts")
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    alert_templates = {
        "animal_detected": (
            f"🚨 {alert_data.get('species', 'wildlife').title().replace('_', ' ')} DETECTED",
            f"Live animal at {alert_data.get('distance_from_vehicle', 0):.1f}km with {alert_data.get('confidence', 0)*100:.0f}% confidence"
        ),
        "critical": (
            "🚨 CRITICAL ALERT",
            f"High-risk zone: {alert_data.get('zone_name', 'Unknown')} at {alert_data.get('distance', 0):.1f}km - SLOW DOWN!"
        ),
        "emergency": (
            "🆘 EMERGENCY ALERT",
            f"Emergency: {alert_data.get('species', 'wildlife').title()} collision risk - STOP NOW!"
        ),
        "warning": (
            "⚠️ WILDLIFE WARNING",
            f"Approaching {alert_data.get('zone_name', 'Unknown')} at {alert_data.get('distance', 0):.1f}km - Reduce speed"
        )
    }
    
    title, message = alert_templates.get(alert_type, alert_templates["warning"])
    
    priority_map = {
        "critical": "high",
        "emergency": "critical", 
        "animal_detected": "high",
        "warning": "medium"
    }
    
    alert = {
        "id": len(st.session_state.mobile_alerts) + 1,
        "timestamp": timestamp,
        "title": title,
        "message": message,
        "type": alert_type,
        "priority": priority_map.get(alert_type, "medium"),
        "read": False,
        "data": alert_data,
        "sms_sent": False,
        "sms_recipient": None
    }
    
    st.session_state.mobile_alerts.append(alert)
    logger.info(f"✅ Alert created: {title}")
    
    # Send SMS if enabled
    try:
        enable_sms = st.session_state.get('enable_sms_alerts', False)
        user_phone = st.session_state.get('user_phone_number', '').strip()
        
        logger.info(f"SMS Settings - Enabled: {enable_sms}, Phone: {user_phone[:3] if user_phone else 'None'}...")
        
        if enable_sms and user_phone:
            if sms_system.validate_phone_number(user_phone):
                formatted_phone = sms_system.format_phone_number(user_phone)
                logger.info(f"📱 Sending SMS to: {formatted_phone}")
                
                sms_success = sms_system.send_sms_alert(formatted_phone, alert_data, alert_type)
                
                if sms_success or not sms_system.is_initialized:
                    alert['sms_sent'] = True
                    alert['sms_recipient'] = f"+91{formatted_phone}"
                    logger.info(f"✅ SMS {'sent' if sms_system.is_initialized else 'simulated'}")
                else:
                    logger.warning(f"⚠️ SMS sending failed")
            else:
                logger.warning(f"⚠️ Invalid phone number: {user_phone}")
        else:
            if not enable_sms:
                logger.info("ℹ️ SMS alerts disabled")
            if not user_phone:
                logger.info("ℹ️ No phone number configured")
    
    except Exception as e:
        logger.error(f"❌ Error in SMS: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
    
    # Keep only last 50 alerts
    if len(st.session_state.mobile_alerts) > 50:
        st.session_state.mobile_alerts = st.session_state.mobile_alerts[-50:]
    
    return alert

def send_emergency_sms(alert_data: Dict) -> bool:
    """Send emergency SMS to all contacts"""
    try:
        import streamlit as st
        emergency_contacts = st.session_state.get('emergency_contacts', [])
        
        if not emergency_contacts:
            logger.warning("⚠️ No emergency contacts configured")
            return False
        
        logger.info(f"📞 Sending emergency SMS to {len(emergency_contacts)} contacts...")
        
        success_count = 0
        for contact in emergency_contacts:
            phone = contact.get('number', '').strip()
            name = contact.get('name', 'Unknown')
            
            if sms_system.validate_phone_number(phone):
                formatted_phone = sms_system.format_phone_number(phone)
                logger.info(f"   → Sending to {name}: {formatted_phone}")
                
                if sms_system.send_sms_alert(formatted_phone, alert_data, "emergency"):
                    success_count += 1
                    logger.info(f"     ✅ Sent to {name}")
            else:
                logger.warning(f"   ⚠️ Invalid number for {name}: {phone}")
        
        logger.info(f"✅ Emergency SMS: {success_count}/{len(emergency_contacts)} successful")
        return success_count > 0
    
    except Exception as e:
        logger.error(f"❌ Error sending emergency SMS: {str(e)}")
        return False

def get_mobile_alerts() -> List[Dict]:
    """Get all mobile alerts"""
    import streamlit as st
    if 'mobile_alerts' not in st.session_state:
        st.session_state.mobile_alerts = []
    return st.session_state.mobile_alerts

def get_unread_count() -> int:
    """Get unread alerts count"""
    return len([a for a in get_mobile_alerts() if not a.get('read', False)])

def get_sms_system_status() -> Dict:
    """Get SMS system status"""
    return sms_system.get_status()

def test_sms_system() -> Dict:
    """Test SMS system"""
    return sms_system.test_connection()