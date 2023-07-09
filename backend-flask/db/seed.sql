-- this file was manually created
INSERT INTO public.users (display_name,email, handle, cognito_user_id)
VALUES
  ('Anakin Skywalker','rudy.bacoor@gmail.com', 'TheChosenOne' ,'MOCK'),
  ('Testuser','aynfrancesco@gmail.com', 'testuser' ,'MOCK'),
  ('Andrew Bayko','deadly.spotnick@gmail.com', 'krappa' ,'MOCK'),
  ('Londo Mollari', 'lmollari@centari.com', 'londo','MOCK');
INSERT INTO public.activities (user_uuid, message, expires_at)
VALUES
  (
    (SELECT uuid from public.users WHERE users.handle = 'TheChosenOne' LIMIT 1),
    'This was imported as seed data!',
    current_timestamp + interval '10 day'
  )



