import { useState } from 'react';
import { RefreshCw, X } from 'lucide-react';
import { api } from '../../lib/api';

interface UploadModelProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (message: string) => void;
  onError: (message: string) => void;
  authToken?: string;
}

/**
 * Retrain dialog. This replaced "upload a .pkl model": loading an uploaded
 * pickle executes whatever code it contains, so the server now trains its own
 * models from stored data instead of accepting model files.
 */
export default function UploadModel({ isOpen, onClose, onSuccess, onError }: UploadModelProps) {
  const [isWorking, setIsWorking] = useState(false);

  if (!isOpen) return null;

  const handleRetrain = async () => {
    setIsWorking(true);
    try {
      await api.retrain();
      onSuccess('Retraining started. The model card updates when it finishes (about a minute).');
      onClose();
    } catch (error) {
      onError(error instanceof Error ? error.message : 'Could not start retraining');
    } finally {
      setIsWorking(false);
    }
  };

  return (
    <div className="fixed inset-0 z-[60] flex items-center justify-center">
      <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" onClick={onClose} />

      <div className="relative bg-white rounded-xl shadow-2xl w-full max-w-md mx-4 overflow-hidden">
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">Retrain forecasting models</h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
            aria-label="Close modal"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-6 space-y-3 text-sm text-gray-700">
          <p>
            Retrains the 7, 14 and 30-day forecasters with time-ordered cross-validation, and
            only swaps them in once training succeeds.
          </p>
          <p className="text-gray-500">
            Until every tracked series has enough live history (60 days by default), training
            uses the synthetic bootstrap data, and the model card says which was used.
          </p>
        </div>

        <div className="flex items-center justify-end gap-3 px-6 py-4 bg-gray-50 border-t border-gray-200">
          <button
            onClick={onClose}
            disabled={isWorking}
            className="px-4 py-2 text-sm font-medium text-gray-700 hover:text-gray-900 disabled:opacity-50"
          >
            Cancel
          </button>
          <button
            onClick={handleRetrain}
            disabled={isWorking}
            className="px-6 py-2 text-sm font-medium text-white bg-gradient-to-r from-blue-500 to-blue-600 rounded-lg hover:shadow-lg disabled:opacity-50"
          >
            <span className="flex items-center gap-2">
              <RefreshCw className={`w-4 h-4 ${isWorking ? 'animate-spin' : ''}`} />
              {isWorking ? 'Starting…' : 'Retrain now'}
            </span>
          </button>
        </div>
      </div>
    </div>
  );
}
