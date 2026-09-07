import React from 'react';
import { AlertTriangle } from 'lucide-react';
import './ConfirmationModal.css';

const ConfirmationModal = ({
    isOpen,
    onClose,
    onConfirm,
    title = "Confirm Action",
    message = "Are you sure you want to proceed?",
    confirmText = "Confirm",
    cancelText = "Cancel",
    isDanger = false
}) => {
    if (!isOpen) return null;

    const handleBackdropClick = (e) => {
        if (e.target.classList.contains('confirmation-modal-backdrop')) {
            onClose();
        }
    };

    return (
        <div className="confirmation-modal-backdrop" onClick={handleBackdropClick}>
            <div className="confirmation-modal-container">
                <div className={`confirmation-modal-icon ${isDanger ? 'confirmation-modal-icon-danger' : ''}`}>
                    <AlertTriangle size={30} />
                </div>
                <h2 className="confirmation-modal-title">{title}</h2>
                <p className="confirmation-modal-message">{message}</p>

                <div className="confirmation-modal-actions">
                    <button
                        className="confirmation-btn confirmation-btn-cancel"
                        onClick={onClose}
                    >
                        {cancelText}
                    </button>
                    <button
                        className={`confirmation-btn ${isDanger ? 'confirmation-btn-danger' : 'confirmation-btn-primary'}`}
                        onClick={onConfirm}
                    >
                        {confirmText}
                    </button>
                </div>
            </div>
        </div>
    );
};

export default ConfirmationModal;
