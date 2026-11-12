import apiClient from "./apiClient";

const CHECKOUT_SRC = "https://checkout.razorpay.com/v1/checkout.js";

export const loadRazorpayCheckout = () =>
  new Promise((resolve, reject) => {
    if (window.Razorpay) return resolve(true);
    const script = document.createElement("script");
    script.src = CHECKOUT_SRC;
    script.onload = () => resolve(true);
    script.onerror = () => reject({ message: "Could not load the payment window. Check your connection." });
    document.body.appendChild(script);
  });

const paymentApi = {
  createOrder: (courseId) => apiClient(`/payments/courses/${courseId}/order`, { method: "POST" }),
  verify: (payload) => apiClient("/payments/verify", { method: "POST", data: payload }),
  cancel: (razorpayOrderId) =>
    apiClient("/payments/cancel", { method: "POST", data: { razorpay_order_id: razorpayOrderId } }),
};

/**
 * Opens Razorpay Checkout for a paid course.
 * The amount comes from the server order, never from the client.
 * Resolves when the server has verified the payment and enrolled the student.
 * Rejects with { cancelled: true } if the student closes the window.
 */
export const payForCourse = async (course, prefill = {}) => {
  await loadRazorpayCheckout();
  const order = await paymentApi.createOrder(course.id);

  return new Promise((resolve, reject) => {
    const rzp = new window.Razorpay({
      key: order.keyId,
      order_id: order.orderId,
      amount: order.amount,
      currency: order.currency,
      name: "LMS",
      description: order.courseTitle,
      prefill,
      handler: async (response) => {
        try {
          resolve(await paymentApi.verify(response));
        } catch (err) {
          reject(err);
        }
      },
      modal: {
        ondismiss: async () => {
          try {
            await paymentApi.cancel(order.orderId);
          } catch {
            /* order stays "created" and can expire; nothing was charged */
          }
          reject({ cancelled: true, message: "Payment cancelled." });
        },
      },
    });
    rzp.on("payment.failed", (resp) => {
      reject({ message: resp?.error?.description || "Payment failed. You were not charged for enrollment." });
    });
    rzp.open();
  });
};

export default paymentApi;
