
import qrcode
import os
from PIL import Image

def generate_home_page_qr():
    """Generate a QR code that links to the treasure hunt home page"""
    
    # Your deployed app URL - replace with your actual deployment URL
    home_url = "https://your-repl-name.replit.app"
    
    # Create QR code instance
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    
    # Add data to QR code
    qr.add_data(home_url)
    qr.make(fit=True)
    
    # Create QR code image
    qr_img = qr.make_image(fill_color="black", back_color="white")
    
    # Save the QR code
    if not os.path.exists('static'):
        os.makedirs('static')
    
    qr_img.save('static/treasure_hunt_qr.png')
    print(f"QR code generated and saved as 'static/treasure_hunt_qr.png'")
    print(f"QR code points to: {home_url}")
    print("\nTo use:")
    print("1. Deploy your app on Replit")
    print("2. Update the 'home_url' variable with your actual deployment URL")
    print("3. Run this script again to generate the final QR code")
    print("4. Share the QR code image with others")
    
    return qr_img

if __name__ == "__main__":
    generate_home_page_qr()
