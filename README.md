# Google Calendar Integration Solution via AWS Lambda

This solution enables integration between an application and **Google Calendar** using the **OAuth 2.0** service for authentication. Through **AWS Lambda** functions and **API Gateway**, users can authenticate with Google, grant access permissions to their Google Calendar, and store access tokens in your **Amazon S3**. This allows for the use of Google Calendar services, such as creating, reading, and managing events from the user's calendar.

## Features

- **Secure Authentication:** Utilizes OAuth 2.0 to ensure secure access to Google Calendar.
- **Secure Storage:** OAuth tokens (access token and refresh token) are securely stored in Amazon S3.
- **Scope Support:** Allows access to different scopes of the Google Calendar API, including reading and creating events.
- **Redirection and Callback:** Manages the authentication flow and token exchange through appropriate redirections.
- **Success Interface:** Returns a simple interface to the user to indicate successful authentication.

## How the Solution Works

1. **Authorization Request:**
   - The user clicks a button to connect to Google Calendar and is redirected to the Google login page with an **authorization URL**.
   - After logging in, the user grants the necessary permissions (scopes).

2. **Redirection to Callback:**
   - After authorization, Google redirects the user to a Lambda function configured to receive the **authorization code** and the **user_id** (in the `state` of the request).
   - This code is used to obtain the access tokens.

3. **Code Exchange for Tokens:**
   - The callback Lambda uses the **Google OAuth** library to exchange the authorization code for **access tokens** and **refresh tokens**.
   - The tokens are stored in **Amazon S3**, associated with the user who authorized access.

4. **Success Page:**
   - The Lambda returns an HTML page that informs the user of the successful connection, after that, you are all ready to use the Google Calendar API with the user stored tokens.

## AWS Implementation with Terraform

This solution has been fully implemented on AWS using **Terraform**. Below are the details on how to configure and use Terraform to provision the necessary resources.

### 1. Prerequisites
- Install [Terraform](https://www.terraform.io/downloads.html).
- Install [AWS CLI](https://aws.amazon.com/cli/).
- Configure AWS credentials in your local environment.

### 2. Running Terraform
To provision the resources, run the following commands in the command line:

```bash
terraform init
terraform apply
```

### 3. Obtain the API Gateway Link
After the `terraform apply` command, Terraform will provide the defined outputs, including the link to the API Gateway. Use this link to configure the redirect URI in Google Cloud. If you can't find the link, you can obtain it through the AWS console.

## Google Cloud Configuration for OAuth

To ensure proper functionality of OAuth 2.0 authentication, follow the steps below to configure Google Cloud:

### 1. Enable the Google Calendar API
- Access the **Google Cloud Console** ([cloud.google.com](https://cloud.google.com)).
- In the APIs menu, search for **Google Calendar API** and enable it for your project.

### 2. Create OAuth 2.0 Credentials
- In the **Google Cloud Console**, go to **APIs & Services** > **Credentials**.
- Click on **Create Credentials** and select **OAuth Client ID**.
- Choose **Web Application** as the application type.
- Name your client ID.
- In **Authorized redirect URIs**, add the URI of your Lambda function that handles the authorization callback, provided by the **API Gateway**, after running Terraform. It should look like:

  ```
  https://<api-gateway-id>.execute-api.<region>.amazonaws.com/google-calendar-credentials-callback
  ```

- In **Authorized JavaScript origins**, add the origin of your **API Gateway** (without a route).

    ```
    https://<api-gateway-id>.execute-api.<region>.amazonaws.com
    ```

- Click **Create**.
- Download the generated credentials file, rename it to `client_secret.json`, and **move it to the root folder of both Lambdas (authorization and callback)**.

### 3. Configure OAuth Scopes
During the creation of the OAuth client, specify the necessary scopes for access to Google Calendar:
- `https://www.googleapis.com/auth/calendar` (Full access to Calendar).

### 4. Allow Test Users or Publish the App
- While the application is in development, add email addresses of **permitted users** for testing.
- If you want to make the app available to everyone, follow the **publication** process of the app on Google, ensuring it meets the requirements to pass OAuth verification.
