import React from 'react';
import { GoogleLogin } from '@react-oauth/google';

interface GoogleSignInButtonProps {
  onSuccess: (credential: string) => Promise<void>;
  onError?: () => void;
  className?: string;
}

const GoogleSignInButton: React.FC<GoogleSignInButtonProps> = ({
  onSuccess,
  onError,
  className = '',
}) => {
  return (
    <div className={className}>
      <GoogleLogin
        onSuccess={async (response) => {
          if (response.credential) {
            await onSuccess(response.credential);
          } else if (onError) {
            onError();
          }
        }}
        onError={() => onError?.()}
        useOneTap={false}
        theme="filled_black"
        size="medium"
        shape="rectangular"
        text="continue_with"
      />
    </div>
  );
};

export default GoogleSignInButton;
