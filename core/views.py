from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.mail import send_mail
from .models import ContactMessage

# Create your views here.
def home(request):
    return render(request, 'core/home.html')

def about(request):
    return render(request, 'core/about.html')

def contact(request):

    if request.method == "POST":

        name = request.POST.get("name")
        email = request.POST.get("email")
        phone = request.POST.get("phone")
        category = request.POST.get("category")
        message_text = request.POST.get("message")

        # Save to database
        # pyrefly: ignore [missing-attribute]
        ContactMessage.objects.create(
            name=name,
            email=email,
            phone=phone,
            category=category,
            message=message_text
        )

        # Send notification to your company
        send_mail(
            subject=f"New Contact Form Message - {category}",
            message=f"""
Name: {name}
Email: {email}
Phone: {phone}
Category: {category}

Message:
{message_text}
            """,
            from_email=None,
            recipient_list=[email],
            fail_silently=False,
        )

        # Confirmation email to sender
        send_mail(
            subject="We Received Your Message",
            message=f"""
Hello {name},

Thank you for contacting Food Market.

We have received your enquiry and a member of our team
will get back to you shortly.

Category: {category}

Best Regards,
Food Market Support Team
            """,
            from_email=None,
            recipient_list=[email],
            fail_silently=False,
        )

        messages.success(
            request,
            "Your message has been sent successfully. Please check your email for confirmation."
        )

        return redirect("contact")

    return render(request, "core/contact.html")
