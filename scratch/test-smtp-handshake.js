/**
 * Test connecting to smtp.gmail.com:587 with STARTTLS to see the exact network and Google response
 */
const nodemailer = require("nodemailer");

async function testPort587() {
    console.log("--- Testing Network & STARTTLS Handshake on smtp.gmail.com:587 ---");
    const transporter = nodemailer.createTransport({
        host: "smtp.gmail.com",
        port: 587,
        secure: false, // port 587 requires STARTTLS (secure: false)
        requireTLS: true,
        auth: {
            user: "mgowthamkumar472008@gmail.com",
            pass: "test_unauth_pass"
        },
        connectionTimeout: 8000
    });

    try {
        await transporter.verify();
        console.log("SUCCESS");
    } catch (err) {
        console.log("Error Name:", err.name);
        console.log("Error Code:", err.code);
        console.log("Error Command:", err.command);
        console.log("Error ResponseCode:", err.responseCode);
        console.log("Error Response:", err.response);
        console.log("Error Message:", err.message);
    }
}

testPort587();
