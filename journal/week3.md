# Week 3 — Decentralized Authentication


### 1. Setup Cognito UserPool

- Navigated to AWS Console
- Go to AWS Cognito
- Clicked on Create UserPool

![image](https://user-images.githubusercontent.com/56792014/224653510-d506a936-4160-4876-a53b-3443994b62bb.png)

- Configured Password policy, MFA auth, and User Account Recovery. There will be no MFA auth as this will incur cost.

Password Policy

![image](https://user-images.githubusercontent.com/56792014/224653914-d91ad586-1688-4849-9d48-eba4c114288f.png)

MFA

![image](https://user-images.githubusercontent.com/56792014/224654016-b1c51ff2-22ec-493f-903a-42cf1f76f15b.png)

User Account Recovery

![image](https://user-images.githubusercontent.com/56792014/224654161-646c0b17-809a-49b2-b766-20e4cf681f2f.png)


- Self-service sign up will be left on default

![image](https://user-images.githubusercontent.com/56792014/224654861-e9a32c0c-610f-41ab-a5c6-932316bce1e9.png)

- Attribute verification and user account confirmation will be set to Email Address only to save cost.

![image](https://user-images.githubusercontent.com/56792014/224654994-5fe6f068-eb4d-417e-b0dd-071092705f7f.png)

![image](https://user-images.githubusercontent.com/56792014/224655051-509b157f-4456-4e3f-8322-598cdbdd7f4b.png)


- Required attributes would be '**Name**' and '**Preferred_username**.
![image](https://user-images.githubusercontent.com/56792014/224655335-3a9be900-1581-49bb-95ac-843aac8617e0.png)

- Configure message delivery to be only with Cognito 
![image](https://user-images.githubusercontent.com/56792014/224655474-bf7745ad-b79f-438c-89bd-00a7b38d70d4.png)

- Integrate your app, userpool name will be the app name + userpool '**Cruddur-user-pool**'. We will not be using the Cognito Hosted UI as we will use our App's UI 
![image](https://user-images.githubusercontent.com/56792014/224656062-4a093738-3ead-4eff-84e9-c92a66cd4d9a.png)

- App type would be '**Other**'. App client name would be "**Cruddur**". Everything else would be on default
![image](https://user-images.githubusercontent.com/56792014/224656374-6d13b006-e258-4a77-b4ad-76932d15eef2.png)

- After finishing the creation of the User Pool. results should be like this. 

![image](https://user-images.githubusercontent.com/56792014/224656686-2f8e669a-d6b1-4cdd-b378-af4348b565c1.png)



### 2. 	Implement Custom Signin Page

```
import './SigninPage.css';
import React from "react";
import {ReactComponent as Logo} from '../components/svg/logo.svg';
import { Link } from "react-router-dom";


// [TODO] Authenication
//import Cookies from 'js-cookie'
import { Auth } from 'aws-amplify';

export default function SigninPage() {

  const [email, setEmail] = React.useState('');
  const [password, setPassword] = React.useState('');
  const [errors, setErrors] = React.useState('');

  const onsubmit = async (event) => {
    setErrors('')
    event.preventDefault();
      Auth.signIn(email, password)
        .then(user => {
          console.log('user',user)
          localStorage.setItem("access_token", user.signInUserSession.accessToken.jwtToken)
          window.location.href = "/"
        })
        .catch(error => { 
          if (error.code == 'UserNotConfirmedException') {
            window.location.href = "/confirm"
          }
          setErrors(error.message)
        });      
        return false
    }

  const email_onchange = (event) => {
    setEmail(event.target.value);
  }
  const password_onchange = (event) => {
    setPassword(event.target.value);
  }

  let el_errors;
  if (errors){
    el_errors = <div className='errors'>{errors}</div>;
  }

  return (
    <article className="signin-article">
      <div className='signin-info'>
        <Logo className='logo' />
      </div>
      <div className='signin-wrapper'>
        <form 
          className='signin_form'
          onSubmit={onsubmit}
        >
          <h2>Sign into your Cruddur account</h2>
          <div className='fields'>
            <div className='field text_field username'>
              <label>Email</label>
              <input
                type="text"
                value={email}
                onChange={email_onchange} 
              />
            </div>
            <div className='field text_field password'>
              <label>Password</label>
              <input
                type="password"
                value={password}
                onChange={password_onchange} 
              />
            </div>
          </div>
          {el_errors}
          <div className='submit'>
            <Link to="/forgot" className="forgot-link">Forgot Password?</Link>
            <button type='submit'>Sign In</button>
          </div>

        </form>
        <div className="dont-have-an-account">
          <span>
            Don't have an account?
          </span>
          <Link to="/signup">Sign up!</Link>
        </div>
      </div>

    </article>
  );
}
```

- SignIn is working 
![image](https://user-images.githubusercontent.com/56792014/224660168-0f5f25b8-27c3-4a03-8103-5ba5765509a9.png)


### 3. 	Implement Custom Signup Page

```
import './SignupPage.css';
import React from "react";
import {ReactComponent as Logo} from '../components/svg/logo.svg';
import { Link } from "react-router-dom";

import { Auth } from 'aws-amplify';

// [TODO] Authenication
//import Cookies from 'js-cookie'

export default function SignupPage() {

  // Username is Eamil
  const [name, setName] = React.useState('');
  const [email, setEmail] = React.useState('');
  const [username, setUsername] = React.useState('');
  const [password, setPassword] = React.useState('');
  const [errors, setErrors] = React.useState('');

  const onsubmit = async (event) => {
    event.preventDefault();
    setErrors('')
    console.log('username',username)
    console.log('email',email)
    console.log('name',name)
    try {
        const { user } = await Auth.signUp({
          username: email,
          password: password,
          attributes: {
              name: name,
              email: email,
              preferred_username: username,
          },
          autoSignIn: { // optional - enables auto sign in after user is confirmed
              enabled: true,
          }
        });
        console.log(user);
        window.location.href = `/confirm?email=${email}`
    } catch (error) {
        console.log(error);
        setErrors(error.message)
    }
    return false
  }
  

  const name_onchange = (event) => {
    setName(event.target.value);
  }
  const email_onchange = (event) => {
    setEmail(event.target.value);
  }
  const username_onchange = (event) => {
    setUsername(event.target.value);
  }
  const password_onchange = (event) => {
    setPassword(event.target.value);
  }

  let el_errors;
  if (errors){
    el_errors = <div className='errors'>{errors}</div>;
  }

  return (
    <article className='signup-article'>
      <div className='signup-info'>
        <Logo className='logo' />
      </div>
      <div className='signup-wrapper'>
        <form 
          className='signup_form'
          onSubmit={onsubmit}
        >
          <h2>Sign up to create a Cruddur account</h2>
          <div className='fields'>
            <div className='field text_field name'>
              <label>Name</label>
              <input
                type="text"
                value={name}
                onChange={name_onchange} 
              />
            </div>

            <div className='field text_field email'>
              <label>Email</label>
              <input
                type="text"
                value={email}
                onChange={email_onchange} 
              />
            </div>

            <div className='field text_field username'>
              <label>Username</label>
              <input
                type="text"
                value={username}
                onChange={username_onchange} 
              />
            </div>

            <div className='field text_field password'>
              <label>Password</label>
              <input
                type="password"
                value={password}
                onChange={password_onchange} 
              />
            </div>
          </div>
          {el_errors}
          <div className='submit'>
            <button type='submit'>Sign Up</button>
          </div>
        </form>
        <div className="already-have-an-account">
          <span>
            Already have an account?
          </span>
          <Link to="/signin">Sign in!</Link>
        </div>
      </div>
    </article>
  );
}

```


### 4. 	Implement Custom Confirmation Page

-Confirmation after sign up is working
![image](https://user-images.githubusercontent.com/56792014/224660859-5516102e-9998-4044-b5f1-431ead0e6b5d.png)


- Post confirmation in AWS Cognito UI
![image](https://user-images.githubusercontent.com/56792014/224661055-203660f6-3135-4481-b363-1282d3c585d7.png)



### 5. 	Implement Custom Recovery Page

-Recovery email is working. 
![image](https://user-images.githubusercontent.com/56792014/224659672-40ee3500-59a4-4e4e-8808-45c00ef2ec45.png)

-Password reset is confirmed working.
![image](https://user-images.githubusercontent.com/56792014/224659846-57b2b524-d688-412a-b319-3354c7755234.png)



### 6. Backend JWT token 

![image](https://user-images.githubusercontent.com/56792014/224662311-6815662f-965c-41d2-abc3-ddc14d59c7dd.png)
