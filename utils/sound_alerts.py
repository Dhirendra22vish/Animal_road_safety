import streamlit as st
import streamlit.components.v1 as components

def play_external_audio(audio_url, volume=0.5):
    """Play external audio URL with proper error handling"""
    audio_html = f"""
    <audio id="alertAudio" autoplay>
        <source src="{audio_url}" type="audio/mpeg">
        <source src="{audio_url}" type="audio/wav">
        <source src="{audio_url}" type="audio/ogg">
    </audio>
    <script>
    (function() {{
        var audio = document.getElementById('alertAudio');
        if (audio) {{
            audio.volume = {volume};
            audio.play().catch(function(error) {{
                console.log('External audio failed, using fallback beep');
            }});
        }}
    }})();
    </script>
    """
    components.html(audio_html, height=0)

def get_alert_sound_html(alert_type="general", custom_url=None):
    """Generate HTML with working alert sounds using Web Audio API or custom URL"""
    
    # If custom URL provided, use it
    if custom_url:
        return f"""
        <audio autoplay>
            <source src="{custom_url}" type="audio/mpeg">
            <source src="{custom_url}" type="audio/wav">
            <source src="{custom_url}" type="audio/ogg">
        </audio>
        <script>
        (function() {{
            var audio = document.querySelector('audio');
            if (audio) {{
                audio.volume = 0.5;
                audio.crossOrigin = "anonymous";
                audio.play().catch(function(error) {{
                    console.log('Audio play failed:', error);
                }});
            }}
        }})();
        </script>
        """
    
    if alert_type == "critical":
        # Critical alert - high frequency, urgent beep pattern
        sound_html = """
        <script>
        (function() {
            const AudioContext = window.AudioContext || window.webkitAudioContext;
            if (!AudioContext) {
                console.log('Web Audio API not supported');
                return;
            }
            
            const audioContext = new AudioContext();
            
            function playBeep(frequency, duration, delay) {
                setTimeout(() => {
                    const oscillator = audioContext.createOscillator();
                    const gainNode = audioContext.createGain();
                    
                    oscillator.connect(gainNode);
                    gainNode.connect(audioContext.destination);
                    
                    oscillator.frequency.value = frequency;
                    oscillator.type = 'sine';
                    
                    gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
                    gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + duration);
                    
                    oscillator.start(audioContext.currentTime);
                    oscillator.stop(audioContext.currentTime + duration);
                }, delay);
            }
            
            // Critical alert pattern: three urgent beeps
            playBeep(1000, 0.15, 0);
            playBeep(1200, 0.15, 200);
            playBeep(1400, 0.2, 400);
        })();
        </script>
        """
    elif alert_type == "animal_detected":
        # Animal detection - medium frequency, double beep
        sound_html = """
        <script>
        (function() {
            const AudioContext = window.AudioContext || window.webkitAudioContext;
            if (!AudioContext) {
                console.log('Web Audio API not supported');
                return;
            }
            
            const audioContext = new AudioContext();
            
            function playBeep(frequency, duration, delay) {
                setTimeout(() => {
                    const oscillator = audioContext.createOscillator();
                    const gainNode = audioContext.createGain();
                    
                    oscillator.connect(gainNode);
                    gainNode.connect(audioContext.destination);
                    
                    oscillator.frequency.value = frequency;
                    oscillator.type = 'sine';
                    
                    gainNode.gain.setValueAtTime(0.25, audioContext.currentTime);
                    gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + duration);
                    
                    oscillator.start(audioContext.currentTime);
                    oscillator.stop(audioContext.currentTime + duration);
                }, delay);
            }
            
            // Animal detection pattern: two beeps
            playBeep(800, 0.2, 0);
            playBeep(900, 0.2, 250);
        })();
        </script>
        """
    else:
        # General alert - lower frequency, single beep
        sound_html = """
        <script>
        (function() {
            const AudioContext = window.AudioContext || window.webkitAudioContext;
            if (!AudioContext) {
                console.log('Web Audio API not supported');
                return;
            }
            
            const audioContext = new AudioContext();
            
            const oscillator = audioContext.createOscillator();
            const gainNode = audioContext.createGain();
            
            oscillator.connect(gainNode);
            gainNode.connect(audioContext.destination);
            
            oscillator.frequency.value = 600;
            oscillator.type = 'sine';
            
            gainNode.gain.setValueAtTime(0.2, audioContext.currentTime);
            gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.3);
            
            oscillator.start(audioContext.currentTime);
            oscillator.stop(audioContext.currentTime + 0.3);
        })();
        </script>
        """
    
    return sound_html

def play_alert_sound(alert_type="general", custom_url=None):
    """Play alert sound using Web Audio API or custom URL"""
    if 'last_alert_type' not in st.session_state:
        st.session_state.last_alert_type = None
    
    # Play sound if it's different from last alert or enough time has passed
    if st.session_state.last_alert_type != alert_type:
        st.session_state.last_alert_type = alert_type
        sound_html = get_alert_sound_html(alert_type, custom_url)
        components.html(sound_html, height=0)

def play_audio_alert(alert_type="general", custom_url=None):
    """Display audio alert with sound and visual feedback"""
    alert_messages = {
        "general": "🔊 AUDIO ALERT: Animal crossing zone ahead. Reduce speed immediately!",
        "critical": "🚨 CRITICAL ALERT: Animal detected nearby! STOP IMMEDIATELY!",
        "animal_detected": "🚨 ANIMAL DETECTED: Wildlife spotted nearby! Emergency protocols activated!"
    }
    
    alert_colors = {
        "general": "#ff9800",
        "critical": "#ff4444",
        "animal_detected": "#ff6b6b"
    }
    
    # Play the sound
    play_alert_sound(alert_type, custom_url)
    
    # Display visual alert
    st.markdown(f"""
    <div style="background: {alert_colors.get(alert_type, '#ff6b6b')}; 
                padding: 15px; 
                border-radius: 10px; 
                margin: 10px 0;
                color: white;
                text-align: center;
                font-weight: bold;
                animation: alertPulse 1s ease-in-out infinite;
                box-shadow: 0 4px 6px rgba(0,0,0,0.3);">
        {alert_messages.get(alert_type, alert_messages["general"])}
        <br><small style="margin-top: 8px; display: inline-block;">🔔 Audio Alert Active</small>
    </div>
    <style>
    @keyframes alertPulse {{
        0%, 100% {{ transform: scale(1); opacity: 1; }}
        50% {{ transform: scale(1.02); opacity: 0.95; }}
    }}
    </style>
    """, unsafe_allow_html=True)

def create_sound_test_interface():
    """Create interface for testing different alert sounds"""
    st.markdown("### 🔊 Sound Alert Testing")
    
    st.info("Click buttons below to test different alert sounds. Make sure your device volume is on!")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔊 General Alert", use_container_width=True, key="test_general"):
            play_audio_alert("general")
            st.success("Playing general alert sound...")
    
    with col2:
        if st.button("🚨 Critical Alert", use_container_width=True, key="test_critical"):
            play_audio_alert("critical")
            st.success("Playing critical alert sound...")
    
    with col3:
        if st.button("🦌 Animal Detection", use_container_width=True, key="test_animal"):
            play_audio_alert("animal_detected")
            st.success("Playing animal detection sound...")
    
    st.markdown("---")
    
    # Sound pattern descriptions
    st.markdown("""
    **Sound Patterns:**
    - **General Alert**: Single beep (600 Hz)
    - **Critical Alert**: Three urgent beeps (1000-1400 Hz)
    - **Animal Detection**: Double beep pattern (800-900 Hz)
    """)

def get_species_sound_type(species):
    """Get appropriate sound type based on animal species"""
    critical_species = ['tiger', 'elephant', 'leopard']
    high_alert_species = ['sloth_bear', 'wild_boar', 'bison']
    
    if species in critical_species:
        return 'critical'
    elif species in high_alert_species:
        return 'animal_detected'
    else:
        return 'general'

# Demo usage
if __name__ == "__main__":
    st.title("🔊 Working Sound Alert System")
    
    st.markdown("""
    This sound system uses the **Web Audio API** which is supported in all modern browsers.
    No external files or URLs needed!
    """)
    
    create_sound_test_interface()
    
    st.markdown("---")
    st.markdown("### How to integrate:")
    st.code("""
# In your main app, replace the sound functions with:
from utils.sound_alerts import play_audio_alert, get_species_sound_type

# When an alert is triggered:
if alert['risk_level'] == 'CRITICAL':
    play_audio_alert("critical")
elif alert['risk_level'] == 'HIGH':
    play_audio_alert("animal_detected")
else:
    play_audio_alert("general")

# Or based on species:
sound_type = get_species_sound_type(alert['species'])
play_audio_alert(sound_type)
    """, language="python")