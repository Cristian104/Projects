# Vanitas Tool Policy (STABLE PROTOCOL)

## Audio/Media Delivery
To send a voice message, you MUST follow these two steps exactly:
1. Generate the file using python:
   exec python3 /workspace/skills/elevenlabs-voices/scripts/tts.py --text "Message" --voice lucy --output /workspace/voice_msg.mp3
2. Include this exact line at the end of your response:
   MEDIA:/home/jorg/stacks/remastered_bot/voice_msg.mp3

CRITICAL: DO NOT use relative paths for MEDIA:. The gateway will REJECT anything that doesn't start with /home/jorg/stacks/remastered_bot/
