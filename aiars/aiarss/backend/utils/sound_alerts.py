import streamlit as st
import base64
import io

def get_alert_sound(alert_type="general"):
    """Generate base64 encoded alert sounds for different alert types"""
    
    # Base64 encoded short beep sounds (WAV format)
    # These are simple beep sounds that work in web browsers
    if alert_type == "critical":
        # Critical alert - high frequency beep
        sound_html = """
        <audio autoplay>
            <source src="https://commondatastorage.googleapis.com/codeskulptor-assets/jump.ogg" type="audio/mpeg">
        </audio>
        <script>
            var audio = document.querySelector('audio');
            audio.volume = 0.7;
            audio.play().catch(function(e) {
                console.log('Audio play failed:', e);
            });
        </script>
        """
    elif alert_type == "animal_detected":
        # Animal detection - medium frequency beep
        sound_html = """
        <audio autoplay>
            <source src="https://commondatastorage.googleapis.com/codeskulptor-assets/jump.ogg" type="audio/mpeg">
        </audio>
        <script>
            var audio = document.querySelector('audio');
            audio.volume = 0.5;
            audio.play().catch(function(e) {
                console.log('Audio play failed:', e);
            });
        </script>
        """
    else:
        # General alert - low frequency beep
        sound_html = """
        <audio autoplay>
            <source src="https://assets.mixkit.co/sfx/preview/mixkit-software-interface-start-2574.mp3" type="audio/mpeg">
        </audio>
        <script>
            var audio = document.querySelector('audio');
            audio.volume = 0.3;
            audio.play().catch(function(e) {
                console.log('Audio play failed:', e);
            });
        </script>
        """
    
    return sound_html

def play_alert_sound(alert_type="general"):
    """Play alert sound based on alert type"""
    # Only play sound if it's different from the last alert to avoid repetition
    if 'last_alert_type' not in st.session_state or st.session_state.last_alert_type != alert_type:
        st.session_state.last_alert_type = alert_type
        sound_html = get_alert_sound(alert_type)
        st.markdown(sound_html, unsafe_allow_html=True)
        
        # Visual feedback for sound playing
        st.markdown(f"""
        <div style="background: linear-gradient(45deg, #ff6b6b, #ff8e8e); 
                    padding: 10px; 
                    border-radius: 10px; 
                    margin: 10px 0;
                    text-align: center;
                    color: white;
                    font-weight: bold;">
            🔊 {alert_type.replace('_', ' ').title()} ALERT SOUND PLAYING
        </div>
        """, unsafe_allow_html=True)

def play_audio_alert(alert_type="general"):
    """Display audio alert simulation with enhanced visual feedback"""
    alert_messages = {
        "general": "🔊 AUDIO ALERT: Animal crossing zone ahead. Reduce speed immediately!",
        "critical": "🚨 CRITICAL ALERT: Animal detected nearby! STOP IMMEDIATELY!",
        "animal_detected": "🚨 ANIMAL DETECTED: Wildlife spotted nearby! Emergency protocols activated!"
    }
    
    # Play the corresponding sound
    play_alert_sound(alert_type)
    
    # Visual alert with enhanced animation
    st.markdown(f"""
    <div style="background: {'#ff4444' if alert_type == 'critical' else '#ff6b6b'}; 
                padding: 15px; 
                border-radius: 10px; 
                margin: 10px 0;
                color: white;
                text-align: center;
                font-weight: bold;
                animation: pulse 1s infinite;">
        {alert_messages.get(alert_type, alert_messages["general"])}
        <br><small>🔔 Audio Alert Active - Sound Playing</small>
    </div>
    <style>
    @keyframes pulse {{
        0% {{ transform: scale(1); }}
        50% {{ transform: scale(1.02); }}
        100% {{ transform: scale(1); }}
    }}
    </style>
    """, unsafe_allow_html=True)

def create_sound_test_interface():
    """Create interface for testing different alert sounds"""
    st.markdown("### 🔊 Sound Alert Testing")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔊 Test General Alert", use_container_width=True):
            play_audio_alert("general")
    
    with col2:
        if st.button("🚨 Test Critical Alert", use_container_width=True):
            play_audio_alert("critical")
    
    with col3:
        if st.button("🦌 Test Animal Detection", use_container_width=True):
            play_audio_alert("animal_detected")
    
    # Sound settings
    st.markdown("### ⚙️ Sound Settings")
    enable_sounds = st.checkbox("Enable Alert Sounds", value=True)
    sound_volume = st.slider("Alert Volume", 0.1, 1.0, 0.7)
    
    return enable_sounds, sound_volume

def get_species_sound_mapping(species):
    """Get appropriate sound type based on animal species"""
    sound_mapping = {
        'tiger': 'critical',
        'elephant': 'critical', 
        'leopard': 'critical',
        'sloth_bear': 'animal_detected',
        'wild_boar': 'animal_detected',
        'deer': 'general',
        'sambar': 'general',
        'bison': 'animal_detected',
        'nilgai': 'general',
        'birds': 'general'
    }
    return sound_mapping.get(species, 'general')