"use client";

interface ClearUserModalProps {
  isOpen: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}

export default function ClearUserModal({ isOpen, onConfirm, onCancel }: ClearUserModalProps) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/60 z-[100] flex items-center justify-center p-4">
      <div className="bg-white rounded-xl shadow-2xl max-w-md w-full">
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-2xl font-bold text-gray-800">Clear User & Start Fresh?</h2>
        </div>

        {/* Content */}
        <div className="px-6 py-6">
          <div className="space-y-4 text-gray-700">
            <div className="flex items-start gap-3">
              <svg className="w-6 h-6 text-red-500 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
              <div className="flex-1">
                <p className="font-medium text-gray-800 mb-2">
                  This action will permanently delete:
                </p>
                <ul className="list-disc pl-5 space-y-1 text-sm">
                  <li>Your current anonymous user ID</li>
                  <li>All chat history and sessions</li>
                  <li>All local stored data</li>
                  <li>Terms acceptance status</li>
                </ul>
              </div>
            </div>

            <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
              <p className="text-sm text-blue-800">
                <strong>What happens next:</strong> The page will reload with a new user ID, and you'll need to accept the terms again.
              </p>
            </div>

            <p className="text-sm text-gray-600">
              This is useful when switching between different participants in an experiment using the same computer.
            </p>
          </div>
        </div>

        {/* Footer - Action Buttons */}
        <div className="px-6 py-4 border-t border-gray-200 flex gap-3">
          <button
            onClick={onCancel}
            className="flex-1 px-6 py-3 bg-gray-200 hover:bg-gray-300 text-gray-700 font-medium rounded-lg transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={onConfirm}
            className="flex-1 px-6 py-3 bg-red-600 hover:bg-red-700 text-white font-medium rounded-lg transition-colors"
          >
            Yes, Clear & Reset
          </button>
        </div>
      </div>
    </div>
  );
}
