import base64
import hashlib
import time
import paho.mqtt.client as mqtt
from cryptography.fernet import Fernet

class EncryptedChat:
    def __init__(self, passphrase="liban123"):
        if not passphrase or len(passphrase.strip()) == 0:
            raise ValueError("Passphrase kan inte vara tomt.")
        if len(passphrase) < 8:
            raise ValueError("Passphrase måste vara minst 8 tecken lång.")

        self.key = self.generate_key(passphrase)
        self.cipher = Fernet(self.key)
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect

    def generate_key(self, passphrase):
        "Genererar en säker nyckel baserad på passphrasen."
        return base64.urlsafe_b64encode(hashlib.sha256(passphrase.encode()).digest())

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("Ansluten till MQTT-broker!")
        else:
            print(f"Anslutning misslyckades med kod {rc}.")

    def on_disconnect(self, client, userdata, rc):
        print("⚠ Frånkopplad. Försöker återansluta...")
        while True:
            try:
                self.client.reconnect()
                print("Återansluten!")
                break
            except Exception as e:
                print(f"⚠ Återanslutning misslyckades: {e}")
                time.sleep(5)

    def on_message(self, client, userdata, msg):
        "Dekrypterar och visar mottagna meddelanden."
        try:
            decrypted_msg = self.cipher.decrypt(msg.payload).decode()
            print(f" Mottaget: {decrypted_msg}")
        except Exception as e:
            print(f"⚠ Kunde inte dekryptera meddelandet: {e}")

    def connect_and_start(self, broker, port, topic):
        """Ansluter till MQTT-broker och startar chatten."""
        try:
            self.client.connect(broker, port, 60)
        except Exception as e:
            print(f" Fel vid anslutning till broker: {e}")
            return

        if not topic or " " in topic:
            print(" Ogiltigt topic. Se till att den inte är tom eller innehåller mellanslag.")
            return

        self.client.subscribe(topic)
        self.client.loop_start()
        print(" Chatt är igång. Skriv meddelanden nedan. (skriv 'quit' för att avsluta)")

        try:
            while True:
                message = input("Du: ")
                if message.lower() == 'quit':
                    print(" Avslutar chatten...")
                    break
                try:
                    encrypted_msg = self.cipher.encrypt(message.encode('utf-8'))
                    self.client.publish(topic, encrypted_msg)
                except Exception as e:
                    print(f"⚠ Krypteringsfel: {e}")
        except KeyboardInterrupt:
            print("\n Chatten avbröts.")
        finally:
            self.client.loop_stop()
            self.client.disconnect()

if __name__ == "__main__":
    broker = input(" Ange MQTT-broker adress: ")
    
    while True:
        try:
            port = int(input("Ange MQTT-port (1-65535): "))
            if 1 <= port <= 65535:
                break
            else:
                print(" Portnummer måste vara mellan 1 och 65535.")
        except ValueError:
            print("Ogiltig port. Vänligen ange ett nummer.")

    topic = input(" Ange MQTT-topic: ")

    chat = EncryptedChat()
    chat.connect_and_start(broker, port, topic)
