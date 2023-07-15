import './ReplyForm.css';
import React from "react";
import process from 'process';
//import {ReactComponent as BombIcon} from './svg/bomb.svg';
import ActivityContent  from '../components/ActivityContent';
import FormErrors from '../components/FormErrors'
import {post} from '../lib/Requests'

export default function ReplyForm(props) {
  const [count, setCount] = React.useState(0);
  const [message, setMessage] = React.useState('');
  const [errors, setErrors] = React.useState([]);

  const classes = []
  classes.push('count')
  if (240-count < 0){
    classes.push('err')
  }

  const onsubmit = async (event) => {
    event.preventDefault();
    const url = `${process.env.REACT_APP_BACKEND_URL}/api/activities/${props.activity.uuid}/reply`;
    const payload_data = {
      activitiy_uuid: props.activity_uuid,
      message: message
    }
    post(url,payload_data,{
      setErrors: setErrors,
      auth: true,
      success: function(data){
        if (props.setReplies) {
          props.setReplies((current) => [data, ...current]);
        }
      // reset and close the form
      setCount(0);
      setMessage("");
      props.setPopped(false);
    }
  })
}

  const textarea_onchange = (event) => {
    setCount(event.target.value.length);
    setMessage(event.target.value);
  }

  const close = (event)=> {
    if (event.target.classList.contains("reply_popup")) {
      props.setPopped(false)
    }
  }

  let content;
  if (props.activity){
    content = <ActivityContent activity={props.activity} />;
  }


  if (props.popped === true) {
    return (
      <div className="popup_form_wrap reply_popup" onClick={close}>
        <div className="popup_form">
          <div className="popup_heading">
            <div className="popup_title">
              Reply to...
            </div>
          </div>
          <div className="popup_content">
            <div className="activity_wrap">
              {content}
            </div>
            <form 
              className='replies_form'
              onSubmit={onsubmit}
            >
              <textarea
                type="text"
                placeholder="what is your reply?"
                value={message}
                onChange={textarea_onchange} 
              />
              <div className='submit'>
                <div className={classes.join(' ')}>{240-count}</div>
                <button type='submit'>Reply</button>
              </div>
              <FormErrors errors={errors}/>
            </form>
          </div>
        </div>
      </div>
    );
  }
}