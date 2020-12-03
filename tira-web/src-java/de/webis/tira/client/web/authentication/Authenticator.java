package de.webis.tira.client.web.authentication;

import javax.servlet.ServletException;
import javax.servlet.http.HttpServletRequest;

import org.apache.commons.lang.StringUtils;

import com.google.protobuf.TextFormat;

import de.webis.tira.client.web.generated.TiraClientWebMessages.User;
import de.webis.tira.client.web.generated.TiraClientWebMessages.Users;
import de.webis.tira.client.web.storage.UsersStore;

public class Authenticator {

	private static final String USER_WITHOUT_VM = 			
			"users {\n  userPw: \"mon-existing-password\"\n  userName: \"no-vm-assigned\"\n}";
	
	public static final boolean 
	isSignedIn(HttpServletRequest req)
	throws ServletException {
		return Authenticator.signedInUser(req) != null;
	}

	/**
	 * Returns a Tira user object if an existing username was with the Disraptor user header.
	 * 
	 * @param req The incoming request.
	 * @return a Tira user object.
	 * @throws ServletException
	 */
	public static final User
	signedInUser(HttpServletRequest req)
	throws ServletException {
		String userName = req.getHeader("X-Disraptor-User");
		String firstVmGroup = firstVmGroupOrNull(req);
		User ret = null;
		

		if (userName != null && firstVmGroup != null) {
			ret = UsersStore.getUser(firstVmGroup);
		}
		
		if(ret == null && userName != null) {
			ret = userWithoutVM();
		}
		
		return ret;
	}
	
	private static String firstVmGroupOrNull(HttpServletRequest req) {
		return StringUtils.substringBetween(req.getHeader("X-Disraptor-Groups") + ",", "vm-", ",");
	}
	
	private static User
	userWithoutVM() {
		try {
			Users.Builder ub = Users.newBuilder();
			TextFormat.merge(USER_WITHOUT_VM, ub);
			
			return ub.build().getUsers(0);
		} catch (Exception e) {
			throw new RuntimeException(e);
		}
	}
}
