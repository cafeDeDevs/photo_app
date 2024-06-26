import { GoogleOAuthProvider } from '@react-oauth/google'
import GoogleOAuthLoginBtn from './GoogleOAuthLoginBtn'
const googleClientId = import.meta.env.VITE_GOOGLE_OAUTH2_CLIENT_ID

// TODO: Set up where if the User is
// already logged in they are taken to AuthPage
const Login = () => {
    return (
        <>
            <GoogleOAuthProvider clientId={googleClientId}>
                <GoogleOAuthLoginBtn />
            </GoogleOAuthProvider>
        </>
    )
}

export default Login
