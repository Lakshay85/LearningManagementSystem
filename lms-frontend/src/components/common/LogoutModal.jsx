import React from 'react';
import { LogOut, X } from 'lucide-react';
import './LogoutModal.css';

const LogoutModal = ({ isOpen, onClose, onConfirm }) => {
    if (!isOpen) return null;

    const handleBackdropClick = (e) => {
        if (e.target.classList.contains('logout-modal-backdrop')) {
            onClose();
        }
    };

    return (
        <div className="logout-modal-backdrop" onClick={handleBackdropClick}>
            <div className="logout-modal-container">
                <div className="logout-modal-icon">
                    <LogOut size={30} />
                </div>
                <h2 className="logout-modal-title">Confirm Logout</h2>
                <p className="logout-modal-message">Are you sure you want to log out of your account?</p>

                <div className="logout-modal-actions">
                    <button
                        className="logout-btn logout-btn-cancel"
                        onClick={onClose}
                    >
                        Cancel
                    </button>
                    <button
                        className="logout-btn logout-btn-confirm"
                        onClick={onConfirm}
                    >
                        Yes, Log out
                    </button>
                </div>
            </div>
        </div>
    );
};

export default LogoutModal;
