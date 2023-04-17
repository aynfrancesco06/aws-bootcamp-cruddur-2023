import './ProfileForm.css';
import React from "react";
import process from 'process';
import {getAccessToken} from '../lib/CheckAuth';

export default function ProfileForm(props) {
  const [presignedurl,setPresignedurl] = React.useState(0);
  const [bio, setBio] = React.useState(0);
  const [displayName, setDisplayName] = React.useState(0);

  React.useEffect(()=>{
    console.log('useEffects',props)
    setBio(props.profile.bio);
    setDisplayName(props.profile.display_name);
  }, [props.profile])


  const s3uploadkey = async (event)=> {
    console.log('ext',event)
    try {
      const backend_url = 'https://nppsjdqdg6.execute-api.us-east-1.amazonaws.com/avatars/key_upload'
      await getAccessToken()
      const access_token = localStorage.getItem("access_token")
      //const json = {
      //  extension: extension
      //}
      const res = await fetch(backend_url, {
        method: "POST",
        headers: {
          'Origin': 'https://3000-aynfrancesc-awsbootcamp-5wp8u72n3eu.ws-us94.gitpod.io',
          'Authorization': `Bearer ${access_token}`,
          'Accept': 'application/json',
          'Content-Type': 'application/json'
        }
      })
      let data = await res.json();
      if (res.status === 200) {
        console.log('presigned url', data)
        return data.url
      } else {
        console.log(res)
      }
    } catch (err) {
      console.log(err);
    }
  }

  const s3upload = async (event)=> {
    console.log('event',event)
    const file = event.target.files[0]
    const filename = file.name
    const size = file.size
    const type = file.type
    const preview_image_url = URL.createObjectURL(file)
    console.log(filename,size,type)
    const fileparts = filename.split('.')
    const extension = fileparts[fileparts.length-1]
    const presignedurl = await s3uploadkey(extension)
    try {
      console.log('s3upload')
      const backend_url = presignedurl
      const res = await fetch(presignedurl, {
        method: "PUT",
        body: file,
        headers: {
          'Content-Type': type
      }})
      let data = await res.json();
      if (res.status === 200) {
        setPresignedurl(data.url)
      } else {
        console.log(res)
      }
    } catch (err) {
      console.log(err);
    }
  }

  const bio_onchange = (event) => {
    setBio(event.target.value);
  }

  const display_name_onchange = (event) => {
    setDisplayName(event.target.value);
  }

  const close = (event)=> {
    if (event.target.classList.contains("profile_popup")) {
      props.setPopped(false)
    }
  }



  if (props.popped === true) {
    return (
      <div className="popup_form_wrap profile_popup" onClick={close}>
        <form 
          className='profile_form popup_form'
          onSubmit={onsubmit}
        >
          <div className="popup_heading">
            <div className="popup_title">Edit Profile</div>
            <div className='submit'>
              <button type='submit'>Save</button>
            </div>
          </div>
          <div className="popup_content">

          <div className="upload" onClick={s3uploadkey}>
            Upload Avatar
          </div>
          <input type="file" name="avatarupload" onChange={s3upload} />
            
            <div className="field display_name">
              <label>Display Name</label>
              <input
                type="text"
                placeholder="Display Name"
                value={displayName}
                onChange={display_name_onchange} 
              />
            </div>
            <div className="field bio">
              <label>Bio</label>
              <textarea
                placeholder="Bio"
                value={bio}
                onChange={bio_onchange} 
              />
            </div>
          </div>
        </form>
      </div>
    );
  }
}