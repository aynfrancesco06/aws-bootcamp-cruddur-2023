import "./ActivityContent.css";
import { Link } from "react-router-dom";
import {
  format_datetime,
  message_time_ago,
  time_ago, time_future
} from "../lib/DateTimeFormats";
import { ReactComponent as BombIcon } from "./svg/bomb.svg";

export default function ActivityContent(props) {
  let expires_at;
  if (props.activity.expires_at) {
    expires_at = (
      <div
        className="expires_at"
        title={format_datetime(props.activity.expires_at)}
      >
        <BombIcon className="icon" />
        <span className="ago">{time_future(props.activity.expires_at)}</span>
      </div>
    );
  }

  return (
    <div className="activity_content_wrap">
      <Link
        className="activity_avatar"
        to={`/@` + props.activity.handle}
      ></Link>
      <div className="activity_content">
        <div className="activity_meta">
          <Link className="activity_identity">
            <Link className="display_name" to={`/@` + props.activity.handle}>
              {props.activity.display_name}
            </Link>
            <Link className="handle" to={`/@` + props.activity.handle}>
              @{props.activity.handle}
            </Link>
          </Link>
          {/* activity_identity */}
          <div className="activity_times">
            <div
              className="created_at"
              title={format_datetime(props.activity.created_at)}
            >
              <span className="ago">
                {message_time_ago(props.activity.created_at)}
              </span>
            </div>
            {expires_at}
          </div>
          {/* activity_times */}
        </div>
        {/* activity_meta */}
        <div className="message">{props.activity.message}</div>
      </div>
      {/* activity_content */}
    </div>
  );
}
